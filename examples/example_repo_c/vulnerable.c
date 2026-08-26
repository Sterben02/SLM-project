// examples/example_repo_c/vulnerable.c
#include <stdio.h>
#include <string.h>

char* api_key = "sk-proj-1234567890abcdef";  // секрет

void execute_command(char* user_input) {
    char cmd[256];
    sprintf(cmd, "echo %s", user_input);  // инъекция
    system(cmd);  // небезопасно
}

int main() {
    char buffer[10];
    gets(buffer);  // переполнение буфера
    return 0;
}