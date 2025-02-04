# llm-shell-sandbox
A dockerized sandbox for LLMs to run shell commands and code.

To run the application, clone the repository, `cd` into the newly created `llm-shell-sandbox` directory, and run the command `docker compose up --build -d`. You can then access the web interface at `http://localhost:5220`. You may want to change the `MAX_COMMANDS` and `ALLOWED_COMMANDS` options in `main.py` before building the container image, to change the commands the LLM has access to and how many it is allowed to run in accomplishing a given task. The application assumes that you are running ollama on your local system at `http://host.docker.internal:11434`.
