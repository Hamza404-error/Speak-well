#include "PageController.h"

void PageController::home(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback)
{
    drogon::HttpViewData data;
    auto session = req->session();
    auto username = session->getOptional<std::string>("username");
    data.insert("username", username.value_or(""));

    auto resp = drogon::HttpResponse::newHttpViewResponse("HomeView", data);
    callback(resp);
}

void PageController::learn(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback)
{
    drogon::HttpViewData data;
    auto session = req->session();
    auto username = session->getOptional<std::string>("username");
    data.insert("username", username.value_or(""));

    auto resp = drogon::HttpResponse::newHttpViewResponse("LearnView", data);
    callback(resp);
}

void PageController::lesson(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback)
{
    drogon::HttpViewData data;
    auto session = req->session();
    auto username = session->getOptional<std::string>("username");
    auto completed_lessons = session->getOptional<int>("completed_lessons");
    
    data.insert("username", username.value_or(""));
    data.insert("completed_lessons", completed_lessons.value_or(0));

    auto resp = drogon::HttpResponse::newHttpViewResponse("LessonsView", data);
    callback(resp);
}

void PageController::signin(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback)
{
    auto resp = drogon::HttpResponse::newHttpViewResponse("SignInView");
    callback(resp);
}

void PageController::dictionary(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback)
{
    drogon::HttpViewData data;
    auto session = req->session();
    auto username = session->getOptional<std::string>("username");
    data.insert("username", username.value_or(""));
    
    auto resp = drogon::HttpResponse::newHttpViewResponse("DictionaryView", data);
    callback(resp);
}

void PageController::translate(const drogon::HttpRequestPtr& req, std::function<void (const drogon::HttpResponsePtr &)> &&callback)
{
    drogon::HttpViewData data;
    auto session = req->session();
    auto username = session->getOptional<std::string>("username");
    data.insert("username", username.value_or(""));
    
    auto resp = drogon::HttpResponse::newHttpViewResponse("TranslateView", data);
    callback(resp);
}
