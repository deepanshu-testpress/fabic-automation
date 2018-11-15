# fabic-automation

Run the following commands to clone the code.

```
  mkdir testpress
  cd testpress/
  git clone https://github.com/deepanshu-testpress/fabic-automation.git
  cd fabic-automation/
```

Install Fabric using the following command.

```
  sudo apt-get install fabric
```

Open config.py file with any editor you prefer like(vim, nano or sublime) and update all the configurations.

```
  vim config.py
```

that's it. You are ready to go.

**Note:** To run any command you need to use "fab".

Now to see the list of commands you can use
```
  fab --list
 ```
 You can execute any command by using 
```
  fab <<command>>
 ```
 
 example: To update the code and restart the server you can either use a single command. It will execute all the tasks.
 ```
  fab deploy
 ```
 or you can execute all the tasks independently like
```
  fab update
  fab requirements
  fab execute_manage
  fab deploy
 ```
