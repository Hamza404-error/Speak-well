#pragma once
#include <drogon/HttpController.h>

class ApiController : public drogon::HttpController<ApiController>
{
  public:
    METHOD_LIST_BEGIN
    ADD_METHOD_TO(ApiController::login, "/api/login", drogon::Post);
    ADD_METHOD_TO(ApiController::signup, "/api/signup", drogon::Post);
    ADD_METHOD_TO(ApiController::logout, "/api/logout", drogon::Post);
    ADD_METHOD_TO(ApiController::completeLesson, "/api/progress/complete", drogon::Post);
    METHOD_LIST_END

    void login(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback);
    void signup(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback);
    void logout(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback);
    void completeLesson(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback);
};
