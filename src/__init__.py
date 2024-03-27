from .users.controllers import users_router

list_of_routes = [
    users_router,
]


__all__ = [
    "list_of_routes",
]