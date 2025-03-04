# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

## Product vision statement

Our app allows a user to track their food intake and gym exercises so they can stay on track of their fitness and health goals.

## User stories

[Project User Stories and Issues](https://github.com/software-students-spring2025/2-web-app-sweproj2/issues)

## Steps necessary to run the software

1. Create a new file called `.env` in the root directory and copy the environment variables you received into it.

2. Install and run Docker Desktop on your machine

3. Build and start the application using Docker Compose:
```bash
docker-compose build
docker-compose up
```

4. Open your web browser and navigate to:
```
http://localhost:5000
```

To stop the application:
1. Press CTRL+C in the terminal where docker-compose is running
2. Run `docker-compose down` to clean up the containers

## Troubleshooting
- If you see "port already in use" errors, make sure no other applications are using port 5000
- If you can't connect to MongoDB, verify your .env file contains the correct MONGO_URI
- Make sure Docker Desktop is running before trying to start the application

## Task boards

See instructions. Delete this line and place a link to the task boards here.
