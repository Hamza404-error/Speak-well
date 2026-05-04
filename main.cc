#include <drogon/drogon.h>
#include <iostream>

// 1. Abstraction: Creating a clear interface and hiding complex implementation details.
class IServer {
public:
    virtual ~IServer() = default;
    
    // 4. Polymorphism: Pure virtual function to be overridden
    virtual void configure() = 0; 
    virtual void start() = 0;
};

// 2. Encapsulation: Grouping data (host, port) and methods together, protecting internal state.
class BaseServer : public IServer {
protected:
    std::string host_;
    int port_;

public:
    BaseServer(const std::string& host, int port) : host_(host), port_(port) {}

    void start() override {
        configure();
        std::cout << "Server is running... Open http://" << host_ << ":" << port_ << " in your browser." << std::endl;
        drogon::app().addListener(host_, port_);
        drogon::app().run();
    }
};

// 3. Inheritance: SpeakWellServer inherits properties and behaviors from BaseServer.
class SpeakWellServer : public BaseServer {
public:
    SpeakWellServer(const std::string& host, int port) : BaseServer(host, port) {}

    // 4. Polymorphism: Overriding the base class method to provide specific behavior.
    void configure() override {
        // Enable session support
        drogon::app().enableSession(1200);
    }
};

int main() {
    // Instantiate our server using the OOP principles
    SpeakWellServer server("127.0.0.1", 8080);
    
    // Abstracted start call, keeping the main function clean
    server.start();
    
    return 0;
}