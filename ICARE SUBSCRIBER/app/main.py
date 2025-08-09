from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from .routers import subscriber, family_member, subscriber_appointment, subscriber_store, subscriber_dc, subscriber_sp, token
from .db.mysql import init_db
from .db.subscriber_mongodbsession import connect_to_mongodb
from .firebase_config import initialize_firebase_app
import logging
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Icare Subscriber API", 
    description="API for Icare Subscriber", 
    version="1.0.0",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": False,
        "scopes": [],
    },
    openapi_tags=[
        {"name": "Token", "description": "Operations with access and refresh tokens"}
    ],
    openapi_components={
        "securitySchemes": {
            "AccessToken": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Enter your **Access Token** (e.g., **Bearer eyJ...**)"
            },
            "RefreshToken": {
                "type": "apiKey",
                "in": "header",
                "name": "X-Refresh-Token",
                "description": "Enter your **Refresh Token**"
            }
        }
    })

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app.include_router(subscriber.router, prefix="/app", tags=["Subscriber"])
app.include_router(family_member.router, prefix="/app", tags=["Family Member"])
app.include_router(subscriber_appointment.router, prefix="/app", tags=["Subscriber Appointment"])
app.include_router(subscriber_store.router, prefix="/app", tags=["Subscriber Store"])
app.include_router(subscriber_dc.router, prefix="/app", tags=["Subscriber Diagnostics"])
app.include_router(subscriber_sp.router, prefix="/app", tags=["Subscriber Service Provider"])
app.include_router(token.router, prefix="/app", tags=["Token Management"])

#App Health Checkup
@app.get("/health", tags=["Health"], description="Operation related to health")
def health_check():
    """
    Performs a health check for the application.

    This endpoint is used to verify that the application is running and operational. 
    It returns a simple status message indicating the application's health.

    Returns:
        dict: A JSON response containing the status of the application (e.g., {"status": "healthy"}).
    """
    return {"status": "healthy"}

# Startup Event
@app.on_event("startup")
async def on_startup():
    """
    Handles application startup events.

    This function is executed during the application startup phase. It logs a startup message 
    and initializes the MySQL database connection.

    Raises:
        Exception: If any error occurs during database initialization.
    """
    logger.info("App is starting...")
    await init_db() #connectiing the mysql database
    await connect_to_mongodb() #connecting the mongodb database
    await initialize_firebase_app() #initializing the firebase app
    
# Initialize database connection
@app.get("/")
def read_root():
    """
    Displays a welcome message for the root endpoint.

    This function serves as a default route for the application and returns a friendly 
    welcome message to users accessing the root URL.

    Returns:
        dict: A JSON response containing the welcome message (e.g., {"message": "Welcome to the Icare subscriber"}).
    """
    return {"message": "Welcome to the Icare subscriber"}

# Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handles Starlette HTTP exceptions globally.

    This function intercepts HTTP exceptions raised by the application and returns a consistent 
    JSON response with the appropriate status code and error details.

    Args:
        request (Request): The incoming HTTP request.
        exc (StarletteHTTPException): The HTTP exception raised by the application.

    Returns:
        JSONResponse: A JSON response containing the status code and error details.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles request validation errors globally.

    This function intercepts validation errors raised during request parsing and 
    returns a standardized JSON response with error details.

    Args:
        request (Request): The incoming HTTP request.
        exc (RequestValidationError): The validation error raised by the application.

    Returns:
        JSONResponse: A JSON response containing the validation error details.
    """

    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handles unexpected exceptions globally.

    This function catches unhandled exceptions that occur in the application and 
    returns a generic error response to the user.

    Args:
        request (Request): The incoming HTTP request.
        exc (Exception): The exception raised during request processing.

    Returns:
        JSONResponse: A JSON response with a 500 Internal Server Error status and a generic error message.
    """
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )
