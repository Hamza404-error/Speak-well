#include <drogon/drogon.h>
#include <iostream>

int main() {
    // Enable session support
    drogon::app().enableSession(1200);
    
    std::cout << "Server is running... Open http://127.0.0.1:8080 in your browser." << std::endl;
    drogon::app().addListener("127.0.0.1", 8080);
    drogon::app().run();
    
    return 0;
}