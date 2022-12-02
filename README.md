# Wordle Backend Project 2 : API Gateway and Load Balancing

Group 4 team members:
Florentino Becerra, Mark Carbajal, Nicholas Ayson, Nolan O'donnell

Steps to run the project:

1. Initialize the database and start the API:

   sh ./bin/init.sh

2. Populate the data base by running the python script:

   python3 dbpop.py

3. Copy the nginx configuration file to sites-enabled by running:

   sudo cp etc/tutorial.txt /etc/nginx/sites-enabled/tutorial

4. Start the API by running

   foreman start -m user=1,game=3

5. Go to local.gd docs to view and test all the endpoints
   game:   
   http://wordle.local.gd:5100/docs   
   http://wordle.local.gd:5200/docs   
   http://wordle.local.gd:5300/docs   
      
   user:  
   http://wordle.local.gd:5000/docs  

   Using http://tuffix-vm should yield in redirecting all requests over to the appropriate microservices.

Files to turn in:

1. Python source code:

   game.py  
   user.py  


2. Procfile:

   Procfile contains 2 microservices game and user that have no coupling

3. Initialization and population scripts for the databases:

   dbpop.py - populates the database with wordle words  
   game.sql - contains database for game microservice  
   user.sql - contains database for user microservice  
   init.sh - Initializes the databases to be created  

4. Nginx configuration files:

   tutorial.txt

5. Any other necessary configuration files:
   
   correct.json  
   valid.json - both populate the database with dbpop.py file  
   game.toml  
   user.toml - allows the source to connect to the database  








