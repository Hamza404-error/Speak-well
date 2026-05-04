#pragma once

#include <string>

namespace models {

class User {
public:
    User() : username_(""), completed_lessons_(0) {}
    User(const std::string& username) : username_(username), completed_lessons_(0) {}

    const std::string& getUsername() const { return username_; }
    void setUsername(const std::string& username) { username_ = username; }

    int getCompletedLessons() const { return completed_lessons_; }
    void setCompletedLessons(int count) { completed_lessons_ = count; }
    void addCompletedLesson() { completed_lessons_++; }

private:
    std::string username_;
    int completed_lessons_;
};

} // namespace models
