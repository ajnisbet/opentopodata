# Deploying with a custom domain and HTTPS


* Running in background (daemon command instead of make)
* Custom domain (maybe can skip this: just setup with your domain provider)
* Changing port (change docker command, 80 for http, 443 for https, multiple ports for debugging)
* Running on startup (depends on system)
* Security (CORS, maybe an API key in nginx.conf, IP limiting, other server things like firewall)