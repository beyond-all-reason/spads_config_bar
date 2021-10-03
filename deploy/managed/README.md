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

6. Pull the image

```
curl -SLO https://raw.githubusercontent.com/beyond-all-reason/spads_config_bar/f2e61505034eccac7f84ff55cb93b49f147c9388/docker-compose.yml
docker-compose pull
```

7. **OR** Build the image
```
git clone 'https://github.com/badosu/spads_config_bar'
cd spads_config_bar
docker-compose build spads games-updater
```

8. Edit the `docker-compose.yml` file environment variables
9. Run it

```
docker-compose up games-updater
docker-compose up spads
```
