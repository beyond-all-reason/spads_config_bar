# How to run SPADS locally

1. Install and run [uberserver](https://github.com/spring/uberserver).

2. Create users for spads and testing, respectively

3. Configure it:

```
cp .env.sample .env
$EDITOR .env
```

4. Run:

```
docker-compose up games-updater
docker-compose up spads
```
