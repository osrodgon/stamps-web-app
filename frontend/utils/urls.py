from settings import BACKEND_URL

class URLs:
    class Backend:
        login =     f"{BACKEND_URL}/login/"
        logout=     f"{BACKEND_URL}/logoff/"
        signup =    f"{BACKEND_URL}/users/"
        
    class Frontend:
        login =     "/login"
        logout =    "/logout"
        root =      "/"
        signup =    "/signup"