# How to run SPADS locally

1. Install and run [uberserver](https://github.com/spring/uberserver).

2. Create users for spads and testing, respectively

3. Edit the environment variables at `docker-compose.yml`.

4. Run

```
docker-compose up games-updater
docker-compose up spads
```
