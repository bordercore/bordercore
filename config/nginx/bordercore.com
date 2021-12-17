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

    location /.well-known/acme-challenge {
        root /usr/share/nginx/html/letsencrypt;
    }

    location /favicon.ico {
        root /var/www/html;
    }

    location /favicons {

        proxy_pass https://bordercore-blobs.s3.amazonaws.com/django/img/favicons;
        proxy_set_header Host bordercore-blobs.s3.amazonaws.com;
        proxy_intercept_errors on;
        proxy_redirect off;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        error_page 403 =200 /favicons/default.png;

        location /favicons/default.png {
            internal;
            root /var/www/html;
        }

    }

    location / {

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

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

    # git support
    location ~ ^/git(/.*) {

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


    ssl_certificate /etc/letsencrypt/live/blobs.bordercore.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/blobs.bordercore.com/privkey.pem; # managed by Certbot
}

# Proxy cover images. We do this so that we can return a
#  default image if one is missing from S3.
server {

    listen 443;
    listen [::]:443;

    server_name blobs.bordercore.com;

    location / {

        proxy_pass https://bordercore-blobs.s3.amazonaws.com/;
        proxy_set_header Host bordercore-blobs.s3.amazonaws.com;
        proxy_intercept_errors on;
        proxy_redirect off;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Don't serve back a default image if "nodefault=1" is passed in
        if ($args !~ nodefault=1) {
            error_page 403 =200 /default-cover.png;
        }

        location /default-cover.png {
            internal;
            root /var/www/html;
        }

    }

    location /collections/ {

        proxy_pass https://bordercore-blobs.s3.amazonaws.com/collections/;
        proxy_set_header Host bordercore-blobs.s3.amazonaws.com;
        proxy_intercept_errors on;
        proxy_redirect off;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        error_page 403 =200 /default-cover.png;

        location /collections/default-cover.png {
            internal;
            root /var/www/html;
        }

    }

    ssl_certificate /etc/letsencrypt/live/blobs.bordercore.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/blobs.bordercore.com/privkey.pem; # managed by Certbot
}

# Proxy album artwork images. We do this so that we can return a
#  default image if one is missing from S3.
server {

    listen 443;
    listen [::]:443;

    server_name images.bordercore.com;

    location /album_artwork/ {

        proxy_pass https://bordercore-music.s3.amazonaws.com/artwork/;
        proxy_set_header Host bordercore-music.s3.amazonaws.com;
        proxy_intercept_errors on;
        proxy_redirect off;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        error_page 403 =200 /album_artwork/artwork/default-album-artwork.jpg;

        location /album_artwork/artwork/default-album-artwork.jpg {
            internal;
            root /var/www/html;
        }

    }

    ssl_certificate /etc/letsencrypt/live/blobs.bordercore.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/blobs.bordercore.com/privkey.pem; # managed by Certbot
}
