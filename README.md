# llm-shell-sandbox
A dockerized sandbox for LLMs to run shell commands and code.

## Usage
To run the application, clone the repository, `cd` into the newly created `llm-shell-sandbox` directory, and run the command `cp .env.example .env` to create a valid `.env` file. You can then change the environment variables to your desired values, including specifying the ollama model to use, the temperature, context length, and maximum number of commands to run. You can then run the command `docker compose up --build -d` and access the web interface at `http://localhost:5220` (assuming you haven't modified the port in the `.env` file).

## Upcoming Changes & Features
Currently, the application only works well with relatively simple tasks. You can pass additional tasks after each has completed, but it does not work well at accomplishing complex tasks in one shot. Next steps would be to incorporate a context management system to allow for more granular tracking of the state of the task and directory structure, and to make it easier to take actions outside of the shell and run code or use tools created by the LLM
