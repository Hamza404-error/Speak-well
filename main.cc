#include <drogon/drogon.h>
#include <iostream>

int main() {
    // إعداد المسار الرئيسي للموقع
    drogon::app().registerHandler("/",
        [](const drogon::HttpRequestPtr &,
           std::function<void(const drogon::HttpResponsePtr &)> &&callback) {
            
            // 1. تجهيز البيانات الديناميكية (زي المتغيرات اللي بتيجي من الداتا بيز)
            drogon::HttpViewData data;
            data.insert("name", "حمزة");
            data.insert("icpc_solved", 210); // رقم تجريبي

            // 2. إنشاء الرد وربطه بملف الـ CSP اللي صممناه (اسمه HomeView)
            auto resp = drogon::HttpResponse::newHttpViewResponse("HomeView", data);
            
            // 3. إرسال الصفحة للمستخدم
            callback(resp);
        });
    
    // ... الكود القديم الخاص بالصفحة الرئيسية ...

    // إضافة مسار صفحة التعلم
    drogon::app().registerHandler("/learn",
        [](const drogon::HttpRequestPtr &,
           std::function<void(const drogon::HttpResponsePtr &)> &&callback) {
            
            auto resp = drogon::HttpResponse::newHttpViewResponse("LearnView");
            callback(resp);
        });

    drogon::app().registerHandler("/lesson",
    [](const drogon::HttpRequestPtr &,
       std::function<void(const drogon::HttpResponsePtr &)> &&callback) {
        
        auto resp = drogon::HttpResponse::newHttpViewResponse("LessonsView");
        callback(resp);
    });

    drogon::app().registerHandler("/signin",
    [](const drogon::HttpRequestPtr &,
       std::function<void(const drogon::HttpResponsePtr &)> &&callback) {
        
        auto resp = drogon::HttpResponse::newHttpViewResponse("SignInView");
        callback(resp);
    });
    drogon::app().registerHandler("/translate",
    [](const drogon::HttpRequestPtr &,
       std::function<void(const drogon::HttpResponsePtr &)> &&callback) {
        
        auto resp = drogon::HttpResponse::newHttpViewResponse("TranslateView");
        callback(resp);
    });

    // ... باقي الكود (addListener و run) ...
    std::cout << "Server is running... Open http://127.0.0.1:8080 in your browser." << std::endl;
    drogon::app().addListener("127.0.0.1", 8080);
    drogon::app().run();
    
    return 0;
}