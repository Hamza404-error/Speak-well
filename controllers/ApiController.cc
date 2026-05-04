#include "ApiController.h"

void ApiController::login(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback)
{
    auto jsonPtr = req->getJsonObject();
    if (!jsonPtr || !(*jsonPtr)["username"].isString()) {
        auto resp = drogon::HttpResponse::newHttpResponse();
        resp->setStatusCode(drogon::k400BadRequest);
        callback(resp);
        return;
    }

    std::string username = (*jsonPtr)["username"].asString();
    auto session = req->session();
    session->insert("username", username);
    
    // Initialize completed lessons if not present
    if (!session->getOptional<int>("completed_lessons")) {
        session->insert("completed_lessons", 0);
    }

    Json::Value ret;
    ret["status"] = "success";
    auto resp = drogon::HttpResponse::newHttpJsonResponse(ret);
    callback(resp);
}

void ApiController::signup(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback)
{
    auto jsonPtr = req->getJsonObject();
    if (!jsonPtr || !(*jsonPtr)["username"].isString()) {
        auto resp = drogon::HttpResponse::newHttpResponse();
        resp->setStatusCode(drogon::k400BadRequest);
        callback(resp);
        return;
    }

    std::string username = (*jsonPtr)["username"].asString();
    auto session = req->session();
    session->insert("username", username);
    session->insert("completed_lessons", 0); // New user starts at 0

    Json::Value ret;
    ret["status"] = "success";
    auto resp = drogon::HttpResponse::newHttpJsonResponse(ret);
    callback(resp);
}

void ApiController::logout(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback)
{
    auto session = req->session();
    session->erase("username");
    
    Json::Value ret;
    ret["status"] = "success";
    auto resp = drogon::HttpResponse::newHttpJsonResponse(ret);
    callback(resp);
}

void ApiController::completeLesson(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback)
{
    auto session = req->session();
    auto completed = session->getOptional<int>("completed_lessons").value_or(0);
    
    session->insert("completed_lessons", completed + 1);

    Json::Value ret;
    ret["status"] = "success";
    ret["completed_lessons"] = completed + 1;
    auto resp = drogon::HttpResponse::newHttpJsonResponse(ret);
    callback(resp);
}
