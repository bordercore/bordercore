upstream django {
    # fail_timeout=0 means we always retry an upstream even if it failed
    # to return a good HTTP response

    # for UNIX domain socket setups
    # server unix:/tmp/gunicorn.sock fail_timeout=0;

    # for a TCP configuration
    server 127.0.0.1:9000 fail_timeout=0;
}


server {

    listen 80;
    listen 443;
    listen [::]:443;
     
    server_name www.bordercore.com;

    # ssl on;
    # ssl_certificate /etc/letsencrypt/live/bordercore.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/bordercore.com/privkey.pem;

    location /.well-known/acme-challenge {
        root /usr/share/nginx/html/letsencrypt;
    }

    location /favicons {
	      alias             /var/www/html;

        proxy_pass https://bordercore-blobs.s3.amazonaws.com/django/img/favicons;
        proxy_set_header Host bordercore-blobs.s3.amazonaws.com;
        proxy_intercept_errors on;
        proxy_redirect off;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#        proxy_hide_header x-amz-id-2;
#        proxy_hide_header x-amz-request-id;

	error_page 403 /favicons/default.png;
        location = /favicons/default.png {
#	      return 200;
        }

    }
	      
    location / {

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        # proxy_pass http://10.9.0.6:80;

        # we don't want nginx trying to do something clever with
        # redirects, we set the Host: header above already.
        proxy_redirect off;

        proxy_pass http://django;

    }

    access_log /var/log/django/access.log;
    error_log /var/log/django/error.log;
	      
    # Redirect http to https
    # location / {
    #     return 301 https://$host$request_uri;
    # }

    # error_page 404 /404.html;
    #     location = /40x.html {
    # }

    # error_page 500 502 503 504 /50x.html;
    #     location = /50x.html {
    # }

    # git support
    location ~ /git(/.*) {

        auth_basic "Git Repos";
        auth_basic_user_file "/etc/nginx/htpasswd-git";

        fastcgi_pass  localhost:9002;

        error_log     /var/log/nginx/giterror.log;
        include      fastcgi_params;

        fastcgi_param SCRIPT_FILENAME     /usr/lib/git-core/git-http-backend;

        # export all repositories under GIT_PROJECT_ROOT
        fastcgi_param GIT_HTTP_EXPORT_ALL "";
        fastcgi_param REMOTE_USER $remote_user;
        fastcgi_param GIT_PROJECT_ROOT    /home/git;
        fastcgi_param PATH_INFO           $1;

    }

}

#server {
#
#    listen 81;
#    listen [::]:81;
#
#    server_name bordercore.com www.bordercore.com beta.bordercore.com;
#
#    location /.well-known/acme-challenge {
#        root /usr/share/nginx/html/letsencrypt;
#    }
#
#    access_log /tmp/foobar.log;
#
#}

