#pragma once
#include <drogon/HttpController.h>

class PageController : public drogon::HttpController<PageController>
{
  public:
    METHOD_LIST_BEGIN
    ADD_METHOD_TO(PageController::home, "/", drogon::Get);
    ADD_METHOD_TO(PageController::learn, "/learn", drogon::Get);
    ADD_METHOD_TO(PageController::lesson, "/lesson", drogon::Get);
    ADD_METHOD_TO(PageController::signin, "/signin", drogon::Get);
    ADD_METHOD_TO(PageController::dictionary, "/dictionary", drogon::Get);
    ADD_METHOD_TO(PageController::translate, "/translate", drogon::Get);
    METHOD_LIST_END

    void home(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback);
    void learn(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback);
    void lesson(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback);
    void signin(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback);
    void dictionary(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback);
    void translate(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback);
};

