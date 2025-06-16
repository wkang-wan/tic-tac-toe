## Getting Started

### Prerequisites

* [Docker](https://www.docker.com/products/docker-desktop/)
* [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

### Installation & Running the Application

This project is fully containerized. You do not need to have Python or PostgreSQL installed on your local machine to run it.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/wkang-wan/tic-tac-toe.git
    cd tic-tac-toe
    ```

2.  **Build and Run the Services:**
    This single command will build the FastAPI application image and start both the `api` and `db` containers in the background (detached mode).

    ```bash
    docker-compose up --build -d
    ```

3.  **Check the Status:**
    You can verify that both services are running with:
    ```bash
    docker-compose ps
    ```
    You should see both the `api` and `db` services with a "running" or "up" status.

The API is now running and accessible at `http://localhost:8000`. To view the application logs, run `docker-compose logs -f api`. To stop the application, run `docker-compose down`.

## API Usage

The API is self-documenting using OpenAPI standards. Once the application is running, you can access the interactive documentation via your browser:

* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Running the Test Suite

The project includes a comprehensive test suite with both unit and integration tests.

To run the entire test suite in a clean, containerized environment, execute the following command from the project root:

```bash
docker-compose run --rm api pytest
```
