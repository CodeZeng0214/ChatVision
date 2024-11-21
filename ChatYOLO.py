### 2024.11.18
## 此文件即ChatYOLO的主程序，运行此文件可以与ChatYOLO交互


from Robots import ChatRobot


if __name__ == '__main__':

    chat_robot = ChatRobot()
    
    print("开始对话（输入'退出'以结束）：")
    while True:
        user_input = input("你: ")
        if user_input.lower() == '退出':
            break
        #print("ChatYOLO:")
        chat_robot.ChatFrame(question=user_input)