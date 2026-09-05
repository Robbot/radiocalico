# RadioCalico Nginx Deployment Plan

Last reviewed: 5 September 2026

## Recommended architecture

Use the Docker Compose production stack in `docker-compose.pgprod.yml`:

```text
Browser
  |
  v
Nginx :80/:443
  |-- static HTML, CSS, JavaScript, and images
  `-- /api/* --> Flask :5000 --> PostgreSQL
                                  ^
                                  |
                           metadata poller
```

Nginx should be the only service exposed publicly. Flask and PostgreSQL should
remain reachable only on the internal Compose network. Express is unnecessary
for this production configuration.

The HLS audio does not need to pass through Nginx. The frontend obtains the
HTTPS CloudFront stream URL from `/api/stream-url` and the browser connects to
CloudFront directly.

## Work required before deployment

### 1. Require one PostgreSQL password everywhere

In `docker-compose.pgprod.yml`, Flask already requires `POSTGRES_PASSWORD`, but
PostgreSQL and the metadata poller allow the insecure fallback
`radiocalico123`. All three services should use:

```yaml
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}
```

This prevents accidental deployment with a known password and guarantees that
all services receive the same value.

### 2. Run Flask with Gunicorn

`Dockerfile.flask-pg` currently starts Flask's built-in server:

```dockerfile
CMD ["python", "flask_app.py"]
```

Gunicorn is already present in `requirements.txt`. Replace the development
server with a production command similar to:

```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "30", "flask_app:app"]
```

Worker and thread counts should ultimately be tuned for the deployment host.

### 3. Separate database initialization from application startup

`flask_app_postgres.py` calls `init_db()` only inside its
`if __name__ == '__main__'` block. Gunicorn imports `flask_app:app` and will not
run that block.

Before adopting Gunicorn, create one of the following:

- a one-shot Compose database initialization service;
- a dedicated migration command run during deployment; or
- migrations managed by Alembic or Flask-Migrate.

A dedicated migration/init service is the preferred short-term solution.

### 4. Keep the current Nginx configuration scoped to Docker

The repository's `nginx.conf` contains:

```nginx
upstream flask_backend {
    server flask:5000;
}
```

The hostname `flask` resolves only on the Compose network. Likewise,
`/usr/share/nginx/html` is correct because `Dockerfile.nginx` copies `public/`
there. These settings are not suitable for a native host installation without
changes.

## Public deployment requirements

### HTTPS and domain

- Set `server_name` to the actual domain.
- Obtain a TLS certificate, normally with Let's Encrypt.
- Listen on port 443 and redirect port 80 to HTTPS.
- Allow inbound TCP ports 80 and 443 in the host/cloud firewall.
- Point the domain's DNS records at the server.

### Protect mutation endpoints

`POST /api/update-track` is currently unauthenticated. Any public client could
replace the current-track information. It should be removed from the public API
surface, restricted to the internal poller, or protected with an API token.

The rating endpoints should also have Nginx rate limiting. A browser-generated
local-storage user ID is not a strong abuse control and can be replaced by a
client.

### Production hardening

- Pin the `hls.js` dependency rather than loading `hls.js@latest`.
- Prefer serving `hls.js` locally, or add Subresource Integrity when using a
  CDN.
- Do not mark `player.js` and `style.css` as `immutable` unless their filenames
  are content-fingerprinted. Otherwise, remove `immutable` or use a shorter
  cache lifetime.
- Return generic API errors to clients and log detailed exceptions server-side.
- Add appropriate security headers, including a tested Content Security Policy
  once external resources have been inventoried.
- Add request/body limits and rate limits appropriate for the small JSON API.

### Operations

- Add scheduled `pg_dump` backups stored outside the PostgreSQL Docker volume.
- Define and test a restore procedure.
- Monitor container health, restart counts, disk use, and Nginx/Flask errors.
- Configure log retention in addition to the Compose log rotation settings.
- Decide how image updates and application releases will be rolled back.

## Initial deployment commands

After completing the required changes:

```bash
cd /home/roju/src/radiocalico
export POSTGRES_PASSWORD='replace-with-a-long-random-password'
docker compose -f docker-compose.pgprod.yml up -d --build
```

Do not place a real password in shell history on a shared system. For ongoing
operation, use a root-readable environment file or a secrets mechanism
appropriate to the hosting platform.

Verify the stack:

```bash
docker compose -f docker-compose.pgprod.yml ps
docker compose -f docker-compose.pgprod.yml logs --tail=100
curl -i http://localhost/health
curl -i http://localhost/api/test
curl -i http://localhost/api/stream-url
```

Then verify in a browser:

- the page and static assets load;
- the play button starts the HLS stream;
- current and recently played tracks update;
- rating status and rating submission work;
- album art loads without mixed-content or CORS errors.

## Native systemd deployment caveats

Do not run `install-services-pg.sh` on a production host in its current form.
It has the following host-specific or unsafe assumptions:

- It expects `/home/roju/radiocalico`, while this checkout is currently at
  `/home/roju/src/radiocalico`.
- The Nginx upstream is `flask:5000`; native Flask would normally listen on
  `127.0.0.1:5000`.
- It replaces the entire `/etc/nginx/nginx.conf` rather than installing an
  isolated site/server block.
- It assumes the Nginx account is named `nginx`; Debian and Ubuntu commonly use
  `www-data`.
- It creates a second Nginx systemd service rather than using the operating
  system's `nginx.service`.
- It attempts to launch Nginx as an unprivileged account while binding port 80.
- Its Flask service uses the development server rather than Gunicorn.
- Its unit files contain hard-coded user names and paths.
- It writes the database password directly into systemd units and performs an
  unsafe `sed` substitution for passwords containing special characters.
- On newer PostgreSQL versions, database privileges alone may not permit table
  creation in the `public` schema. Make `radiocalico` the database owner or
  grant the necessary schema privileges explicitly.

If native deployment is later required, use the distribution-provided Nginx
service, install an isolated site file, serve static files from a conventional
path such as `/var/www/radiocalico`, run Gunicorn as a separate locked-down
systemd service on `127.0.0.1:5000`, and load secrets from a protected
environment file.

## Recommended implementation order

1. Make PostgreSQL password handling consistent.
2. Add a database initialization or migration command.
3. Replace the Flask development server with Gunicorn.
4. Build the Compose stack and verify its health and application behavior.
5. Configure the production domain and HTTPS.
6. Protect `/api/update-track` and rate-limit write endpoints.
7. Correct static dependency and caching behavior.
8. Add database backups, restore testing, monitoring, and rollback procedures.

## Review notes

- The Compose file passed `docker compose config --quiet` when supplied a
  placeholder password. Docker Compose reported only that the top-level
  `version` attribute is obsolete; it can be removed as cleanup.
- The PostgreSQL Flask application, metadata poller, and installation script
  passed basic language/shell syntax checks.
- The JavaScript test suite could not be executed during the review because
  `node_modules` was absent and `vitest` was unavailable.
