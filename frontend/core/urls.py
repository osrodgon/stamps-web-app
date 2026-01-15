from settings import BACKEND_URL

class URLs:
    class Backend:
        login =             f"{BACKEND_URL}/login/"
        logout =            f"{BACKEND_URL}/logoff/"
        signup =            f"{BACKEND_URL}/users/"
        years =             f"{BACKEND_URL}/years/"
        
    class Frontend:
        collections =       "/collections"
        login =             "/login"
        logout =            "/logout"
        root =              "/"
        signup =            "/signup"
        stamps_manager =    "/admin/stamps/manager"