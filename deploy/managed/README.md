# How to provision in a newly created instance

1. _(optional)_ If using EC2, provision and make sure to use an ECS-optimized AMI image for your region: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html
2. Make sure ports 22 (TCP) and 53200 - 53400 (UDP) are open
3. SSH into the machine
4. Install docker (not necessary if using an ECS-optimzed EC2 instance)
5. Install docker-compose

```
sudo curl -L https://github.com/docker/compose/releases/download/v2.0.1/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

6. Create a `.env` file and edit it:

```
curl -SL https://raw.githubusercontent.com/beyond-all-reason/spads_config_bar/main/.env.sample -o .env
$EDITOR .env
```

7. Pull the image

```
curl -SLO https://raw.githubusercontent.com/beyond-all-reason/spads_config_bar/main/docker-compose.yml
docker-compose pull
```

8. **OR** Build the image
```
git clone 'https://github.com/badosu/spads_config_bar'
cd spads_config_bar
docker-compose build spads games-updater
```

9. Run it

```
docker-compose up games-updater
docker-compose up spads
```
10. Keep your maps/engines/games updated:

```
touch ~/games-updater.log
crontab -e
```

Add: `0,30 * * * * docker-compose run games-updater >> ~/games-updater.log`
