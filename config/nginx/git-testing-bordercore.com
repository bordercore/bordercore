server {

    listen 7000;

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
