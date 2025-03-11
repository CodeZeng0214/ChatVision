## Qt窗口主程序
#from ChatRobot import ChatRobot
from PySide6.QtWidgets import QApplication
import sys


from UI.MainUIs import ChatWindow

app = QApplication(sys.argv)
window = ChatWindow()
window.show()
sys.exit(app.exec())


# chat_robot = ChatRobot()
    
# print("开始对话（输入'退出'或'q'以结束）：")
# while True:
#     user_input = input("你: ")
#     if user_input.lower() == '退出' or user_input.lower() == 'q':
#         break
#     print("ChatIR:", end='')
#     chat_robot.ChatFrame(question=user_input)
#     print('')