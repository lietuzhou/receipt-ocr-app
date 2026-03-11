import base64
import requests
import os
import re
import math
import json
from datetime import datetime  # 新增：导入datetime
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFillRoundFlatButton, MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.core.window import Window

# ====================== 中文字体配置（适配安卓路径） ======================
from kivy.config import Config
Config.set('kivy', 'default_font', 'Chinese')

from kivy.core.text import LabelBase
# 兼容电脑/安卓的字体路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, 'assets', 'msyh.ttc')
LabelBase.register(name='Chinese', fn_regular=FONT_PATH)
# ===========================================================================

# ====================== 核心配置 ======================
WEWORK_CONFIG = {
    "ocr_secret_id": "AKID374xpYBh4StY1IWbkolrsjOtDJEydLqB",
    "ocr_secret_key": "WvCJJE1iFl9fDdrx6A4sWH5nKhv55uXz",
    "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/wedoc/smartsheet/webhook?key=5wdvRBR3mjBHe69teL94DTTqdXPjLcoxzZ51rtljatDO5hIMiLek5Xl7hvCMcnecgabwYBW9ppzdd3hnrrFXAmjEpC4LGBHmu2AyF9fUsxAh",
    "headers": {"Content-Type": "application/json; charset=utf-8"},
    "success_code": 0,
    "success_msg": "提交到企业微信表格成功!",
    "field_mapping": {
        "no": "ftQMc5",
        "name": "ftk5Tx",
        "qty": "fi17hF",
        "batch": "fHavw8",
        "date": "f04Gwj"
    }
}

# ===============================================================
KV = '''
FloatLayout:
    MDBoxLayout:
        id: btn_container
        orientation: 'horizontal'
        size_hint: 0.8, 0.4
        pos_hint: {'center_x': 0.5, 'y': 0.1}
        spacing: 20
        
        MDFillRoundFlatButton:
            text: "拍照"
            size_hint_y: None
            height: 60
            md_bg_color: "#4CAF50"
            font_size: 20
            font_name: 'Chinese'
            on_press: app.take_photo()
        
        MDFillRoundFlatButton:
            text: "选择照片"
            size_hint_y: None
            height: 60
            md_bg_color: "#2196F3"
            font_size: 20
            font_name: 'Chinese'
            on_press: app.choose_image()
'''

class EditableLabel(Label):
    """可编辑标签类"""
    def __init__(self, prefix, key, **kwargs):
        kwargs['font_name'] = 'Chinese'
        super().__init__(**kwargs)
        self.prefix = prefix
        self.key = key
        self.content = ""
        self.edit_input = None
        self.app = None

    def update_content(self, new_content):
        self.content = new_content.strip()
        self.text = f"{self.prefix}{self.content}" if self.content else ""

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.edit_input and self.content:
            self._create_edit_input()
            return True
        return super().on_touch_down(touch)

    def _create_edit_input(self):
        x, y = self.pos
        width, height = self.size

        self.edit_input = TextInput(
            text=self.content,
            pos=(x, y),
            size=(width, height),
            size_hint=(None, None),
            font_size=self.font_size,
            font_name='Chinese',
            foreground_color=(1, 0, 0, 1),
            background_color=(1, 1, 1, 0.5),
            cursor_color=(0, 0, 0, 1),
            multiline=False,
            halign=self.halign,
        )

        self.edit_input.bind(on_text_validate=self._save_edit)
        self.edit_input.bind(on_touch_down=self._check_focus_loss)
        self.parent.add_widget(self.edit_input)
        self.edit_input.focus = True
        self.opacity = 0

    def _save_edit(self, *args):
        if not self.edit_input:
            return
        new_content = self.edit_input.text.strip()
        if new_content:
            self.update_content(new_content)
            if self.app:
                self.app.ocr_result[self.key]["text"] = new_content
        self.parent.remove_widget(self.edit_input)
        self.edit_input = None
        self.opacity = 1

    def _check_focus_loss(self, instance, touch):
        if not instance.collide_point(*touch.pos):
            self._save_edit()

class ReceiptApp(MDApp):
    ocr_result = {
        "no": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0},
        "name": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0},
        "qty": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0},
        "batch": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0},
        "date": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0}
    }
    current_img_path = ""
    preview_layout = None
    img_width = 0
    img_height = 0
    x_slope = 0
    x_intercept = 0
    y_slope = 0
    y_intercept = 0
    correction_ready = False

    def build(self):
        # 仅在Windows电脑端设置窗口尺寸，安卓自动适配
        if os.name == 'nt':
            Window.size = (360, 640)
            Window.minimum_width = 360
            Window.minimum_height = 640
        self.dialog = None
        return Builder.load_string(KV)

    # 拍照（适配安卓存储路径）
    def take_photo(self):
        try:
            from plyer import camera
            from plyer import storagepath
            # 安卓用外部存储目录，避免权限问题
            save_path = os.path.join(storagepath.get_external_storage_dir() if os.name != 'nt' else '.', 'receipt.jpg')
            camera.take_picture(filename=save_path, on_complete=self.on_image_selected)
        except Exception as e:
            self.show_dialog(f"相机错误: {str(e)}")

    # 选择照片
    def choose_image(self):
        try:
            from plyer import filechooser
            filechooser.open_file(
                filters=[("Image Files", "*.jpg;*.png;*.jpeg")],
                on_selection=self.on_file_selected
            )
        except Exception as e:
            self.show_dialog(f"文件选择错误: {str(e)}")

    def on_file_selected(self, selection):
        if selection:
            self.on_image_selected(selection[0])

    # 图片选择完成
    def on_image_selected(self, img_path):
        if not os.path.exists(img_path):
            self.show_dialog("未找到图片!")
            return
        
        self.current_img_path = img_path
        self.root.ids.btn_container.opacity = 0
        
        self.preview_layout = FloatLayout(size_hint=(1,1))
        
        # 延迟导入PIL，避免打包冲突
        from PIL import Image as PILImage
        pil_img = PILImage.open(img_path)
        self.img_width, self.img_height = pil_img.size
        
        img_widget = Image(
            source=img_path,
            size_hint=(0.9, 0.7),
            pos_hint={'center_x':0.5, 'center_y':0.6},
            allow_stretch=True,
            keep_ratio=True
        )
        self.preview_layout.add_widget(img_widget)

        # 创建可编辑标签
        self.no_label = EditableLabel(prefix="单号: ", key="no", size_hint=(None,None), size=(200,30), color=(1,0,0,1), font_size=16, bold=True)
        self.name_label = EditableLabel(prefix="品名: ", key="name", size_hint=(None,None), size=(200,30), color=(1,0,0,1), font_size=16, bold=True)
        self.qty_label = EditableLabel(prefix="数量: ", key="qty", size_hint=(None,None), size=(200,30), color=(1,0,0,1), font_size=16, bold=True)
        self.batch_label = EditableLabel(prefix="批次: ", key="batch", size_hint=(None,None), size=(200,30), color=(1,0,0,1), font_size=16, bold=True)
        self.date_label = EditableLabel(prefix="日期: ", key="date", size_hint=(None,None), size=(200,30), color=(1,0,0,1), font_size=16, bold=True)
        
        self.no_label.app = self
        self.name_label.app = self
        self.qty_label.app = self
        self.batch_label.app = self
        self.date_label.app = self
        
        self.preview_layout.add_widget(self.no_label)
        self.preview_layout.add_widget(self.name_label)
        self.preview_layout.add_widget(self.qty_label)
        self.preview_layout.add_widget(self.batch_label)
        self.preview_layout.add_widget(self.date_label)

        # 按钮容器
        btn_box = BoxLayout(size_hint=(0.8, None), height=60, pos_hint={'center_x':0.5, 'y':0.1}, spacing=10)
        self.submit_btn = MDFillRoundFlatButton(
            text="提交到企微表格",
            size_hint=(0.7, 1),
            md_bg_color="#FF9800", 
            font_size=20,
            font_name='Chinese',
            on_press=self.submit_to_wework_table
        )
        self.cancel_btn = MDFillRoundFlatButton(
            text="取消",
            size_hint=(0.3, 1),
            md_bg_color="#F44336", 
            font_size=16,
            font_name='Chinese',
            on_press=self.cancel_operation
        )
        
        btn_box.add_widget(self.submit_btn)
        btn_box.add_widget(self.cancel_btn)
        self.preview_layout.add_widget(btn_box)
        self.root.add_widget(self.preview_layout)
        
        Clock.schedule_once(lambda x: self.ocr_recognize(img_path), 1)

    # 取消操作
    def cancel_operation(self, instance):
        self.reset_interface()

    # 坐标矫正
    def _calculate_coordinate_correction(self, ref_points):
        self.correction_ready = False
        ref_voucher = ref_points.get("参考凭证", {})
        no_text = ref_points.get("No", {})
        receive_factory = ref_points.get("收货工厂", {})
        
        if not all([ref_voucher.get("x"), ref_voucher.get("y"), no_text.get("x"), no_text.get("y"), receive_factory.get("x"), receive_factory.get("y")]):
            self.show_dialog("无法找到足够的参考点进行坐标矫正，将使用原始坐标")
            return
        
        try:
            x1, y1 = ref_voucher["x"], ref_voucher["y"]
            x2, y2 = no_text["x"], no_text["y"]
            if x2 - x1 != 0:
                self.x_slope = (y2 - y1) / (x2 - x1)
                self.x_intercept = y1 - self.x_slope * x1
            else:
                self.x_slope = 0
                self.x_intercept = y1
            
            x3, y3 = receive_factory["x"], receive_factory["y"]
            if x3 - x1 != 0:
                self.y_slope = (y3 - y1) / (x3 - x1)
                self.y_intercept = y1 - self.y_slope * x1
            else:
                self.y_slope = float('inf')
                self.y_intercept = x1
            
            self.correction_ready = True
        except Exception as e:
            self.show_dialog(f"坐标矫正计算失败: {str(e)}")

    def _correct_coordinate(self, x, y):
        if not self.correction_ready:
            return x, y
        try:
            a1, b1, c1 = self.x_slope, -1, self.x_intercept
            corrected_y = abs(a1 * x + b1 * y + c1) / math.sqrt(a1**2 + b1**2)
            
            if self.y_slope == float('inf'):
                corrected_x = abs(x - self.y_intercept)
            else:
                a2, b2, c2 = self.y_slope, -1, self.y_intercept
                corrected_x = abs(a2 * x + b2 * y + c2) / math.sqrt(a2**2 + b2**2)
            
            return corrected_x, corrected_y
        except Exception as e:
            print(f"坐标矫正失败: {e}")
            return x, y

    # OCR识别
    def ocr_recognize(self, img_path):
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
            from tencentcloud.ocr.v20181119 import ocr_client, models

            self.ocr_result = {
                "no": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0},
                "name": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0},
                "qty": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0},
                "batch": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0},
                "date": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0}
            }

            with open(img_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode()

            cred = credential.Credential(WEWORK_CONFIG["ocr_secret_id"], WEWORK_CONFIG["ocr_secret_key"])
            client = ocr_client.OcrClient(cred, "ap-shanghai")
            req = models.GeneralBasicOCRRequest()
            req.ImageBase64 = image_base64
            req.IsWords = True
            resp = client.GeneralBasicOCR(req)

            all_texts = []
            ref_points = {
                "参考凭证": {"x": 0, "y": 0},
                "No": {"x": 0, "y": 0},
                "收货工厂": {"x": 0, "y": 0},
                "品名_表头": {"x": 0, "y": 0},
                "数量_表头": {"x": 0, "y": 0},
                "批次_表头": {"x": 0, "y": 0},
                "点收日期": {"x": 0, "y": 0}
            }

            for item in resp.TextDetections:
                text = item.DetectedText.strip()
                polygon = item.Polygon
                left_top_x = polygon[0].X
                left_top_y = polygon[0].Y
                center_x = (polygon[0].X + polygon[2].X) / 2
                center_y = (polygon[0].Y + polygon[2].Y) / 2
                
                all_texts.append({
                    "text": text,
                    "left_top_x": left_top_x,
                    "left_top_y": left_top_y,
                    "center_x": center_x,
                    "center_y": center_y
                })

                if "参考凭证" in text:
                    ref_points["参考凭证"]["x"] = left_top_x
                    ref_points["参考凭证"]["y"] = left_top_y
                elif any(k in text.upper() for k in ["N0", "NO", "NO."]):
                    ref_points["No"]["x"] = left_top_x
                    ref_points["No"]["y"] = left_top_y
                elif "收货工厂" in text:
                    ref_points["收货工厂"]["x"] = left_top_x
                    ref_points["收货工厂"]["y"] = left_top_y
                elif text in ["品名","晶名"] :
                    ref_points["品名_表头"]["x"] = center_x
                    ref_points["品名_表头"]["y"] = center_y
                elif text in ["数量", "数船"] :
                    ref_points["数量_表头"]["x"] = center_x
                    ref_points["数量_表头"]["y"] = center_y
                elif text in ["批次", "业次"]:
                    ref_points["批次_表头"]["x"] = center_x
                    ref_points["批次_表头"]["y"] = center_y
                elif "点收日期" in text:
                    ref_points["点收日期"]["x"] = center_x
                    ref_points["点收日期"]["y"] = center_y

            self._calculate_coordinate_correction(ref_points)
            ref_voucher_center = (ref_points["参考凭证"]["x"], ref_points["参考凭证"]["y"])
            corrected_ref_voucher = self._correct_coordinate(*ref_voucher_center)
            corrected_product_header = self._correct_coordinate(ref_points["品名_表头"]["x"], ref_points["品名_表头"]["y"])

            for item in all_texts:
                text = item["text"]
                center_x = item["center_x"]
                center_y = item["center_y"]
                corrected_x, corrected_y = self._correct_coordinate(center_x, center_y)
                
                if self.ocr_result["no"]["text"] == "":
                    if "参考凭证" in text or "NO." in text:
                        num_match = re.search(r'(\d{10})', text)
                        if num_match:
                            self.ocr_result["no"]["text"] = num_match.group(1)
                            self.ocr_result["no"]["x"] = center_x
                            self.ocr_result["no"]["y"] = center_y
                            self.ocr_result["no"]["corrected_x"] = corrected_x
                            self.ocr_result["no"]["corrected_y"] = corrected_y
                    elif re.match(r'^\d{10}$', text):
                        distance_to_x_line = abs(corrected_y - corrected_ref_voucher[1])
                        if distance_to_x_line < 30:
                            self.ocr_result["no"]["text"] = text
                            self.ocr_result["no"]["x"] = center_x
                            self.ocr_result["no"]["y"] = center_y
                            self.ocr_result["no"]["corrected_x"] = corrected_x
                            self.ocr_result["no"]["corrected_y"] = corrected_y

                if self.ocr_result["date"]["text"] == "" and (
                        re.match(r'^\d{4}\.\d{2}\.\d{2}$', text) or 
                        re.match(r'^\d{4},\d{2}\.\d{2}$', text) or 
                        re.match(r'^\d{4}.\d{2}\,\d{2}$', text) or 
                        re.match(r'^\d{4},\d{2}\,\d{2}$', text)
                    ):
                    if corrected_y > corrected_ref_voucher[1] + 20 and corrected_y < corrected_ref_voucher[1] + 80:
                        self.ocr_result["date"]["text"] = text
                        self.ocr_result["date"]["x"] = center_x
                        self.ocr_result["date"]["y"] = center_y
                        self.ocr_result["date"]["corrected_x"] = corrected_x
                        self.ocr_result["date"]["corrected_y"] = corrected_y

                if corrected_product_header[1] > 0:
                    if self.ocr_result["name"]["text"] == "" and re.match(r'^\d+$', text):
                        x_diff = abs(corrected_x - corrected_product_header[0])
                        y_diff = corrected_y - corrected_product_header[1]
                        if x_diff < 30 and y_diff > 10 and y_diff < 60:
                            self.ocr_result["name"]["text"] = text
                            self.ocr_result["name"]["x"] = center_x
                            self.ocr_result["name"]["y"] = center_y
                            self.ocr_result["name"]["corrected_x"] = corrected_x
                            self.ocr_result["name"]["corrected_y"] = corrected_y
                    
                    elif self.ocr_result["qty"]["text"] == "" and re.match(r'^\d+,\d+$', text):
                        corrected_qty_header = self._correct_coordinate(ref_points["数量_表头"]["x"], ref_points["数量_表头"]["y"])
                        x_diff = abs(corrected_x - corrected_qty_header[0])
                        y_diff = corrected_y - corrected_product_header[1]
                        if x_diff < 30 and y_diff > 10 and y_diff < 60:
                            self.ocr_result["qty"]["text"] = text
                            self.ocr_result["qty"]["x"] = center_x
                            self.ocr_result["qty"]["y"] = center_y
                            self.ocr_result["qty"]["corrected_x"] = corrected_x
                            self.ocr_result["qty"]["corrected_y"] = corrected_y
                    
                    elif self.ocr_result["batch"]["text"] == "" and re.match(r'^\d+$', text):
                        corrected_batch_header = self._correct_coordinate(ref_points["批次_表头"]["x"], ref_points["批次_表头"]["y"])
                        x_diff = abs(corrected_x - corrected_batch_header[0])
                        y_diff = corrected_y - corrected_product_header[1]
                        if x_diff < 30 and y_diff > 10 and y_diff < 60:
                            self.ocr_result["batch"]["text"] = text
                            self.ocr_result["batch"]["x"] = center_x
                            self.ocr_result["batch"]["y"] = center_y
                            self.ocr_result["batch"]["corrected_x"] = corrected_x
                            self.ocr_result["batch"]["corrected_y"] = corrected_y

            self._update_editable_labels()
            self.position_labels()

        except TencentCloudSDKException as err:
            self.show_dialog(f"OCR识别错误: {err.message}")
        except Exception as e:
            self.show_dialog(f"识别错误: {str(e)}")

    def _update_editable_labels(self):
        self.no_label.update_content(self.ocr_result["no"]["text"])
        self.name_label.update_content(self.ocr_result["name"]["text"])
        self.qty_label.update_content(self.ocr_result["qty"]["text"])
        self.batch_label.update_content(self.ocr_result["batch"]["text"])
        self.date_label.update_content(self.ocr_result["date"]["text"])

    def position_labels(self):
        img_widget = None
        for child in self.preview_layout.children:
            if isinstance(child, Image):
                img_widget = child
                break
        if not img_widget:
            return

        img_display_width = img_widget.width
        img_display_height = img_widget.height
        img_display_x = img_widget.x
        img_display_y = img_widget.y

        scale_x = img_display_width / self.img_width
        scale_y = img_display_height / self.img_height

        if self.ocr_result["no"]["text"] != "":
            use_x = self.ocr_result["no"]["x"]
            use_y = self.ocr_result["no"]["y"]
            label_x = img_display_x + use_x * scale_x - (self.no_label.width / 2)
            label_y = img_display_y + (self.img_height - use_y) * scale_y - 10
            self.no_label.pos = (label_x, label_y)
            
        if self.ocr_result["name"]["text"] != "":
            use_x = self.ocr_result["name"]["x"]
            use_y = self.ocr_result["name"]["y"]
            label_x = img_display_x + use_x * scale_x - (self.name_label.width / 2)
            label_y = img_display_y + (self.img_height - use_y) * scale_y - 10
            self.name_label.pos = (label_x, label_y)
            
        if self.ocr_result["qty"]["text"] != "":
            use_x = self.ocr_result["qty"]["x"]
            use_y = self.ocr_result["qty"]["y"]
            label_x = img_display_x + use_x * scale_x - (self.qty_label.width / 2)
            label_y = img_display_y + (self.img_height - use_y) * scale_y - 10
            self.qty_label.pos = (label_x, label_y)
            
        if self.ocr_result["batch"]["text"] != "":
            use_x = self.ocr_result["batch"]["x"]
            use_y = self.ocr_result["batch"]["y"]
            label_x = img_display_x + use_x * scale_x - (self.batch_label.width / 2)
            label_y = img_display_y + (self.img_height - use_y) * scale_y - 10
            self.batch_label.pos = (label_x, label_y)
            
        if self.ocr_result["date"]["text"] != "":
            use_x = self.ocr_result["date"]["x"]
            use_y = self.ocr_result["date"]["y"]
            label_x = img_display_x + use_x * scale_x - (self.date_label.width / 2)
            label_y = img_display_y + (self.img_height - use_y) * scale_y + 10
            self.date_label.pos = (label_x, label_y)

    # 提交到企微表格
    def submit_to_wework_table(self, instance):
        no_text = self.ocr_result["no"]["text"]
        if not no_text:
            self.show_dialog("点收单号不能为空!")
            return

        try:
            table_data = {}
            field_mapping = WEWORK_CONFIG["field_mapping"]
            
            # 映射字段
            table_data[field_mapping["no"]] = int(no_text) if no_text.isdigit() else no_text
            table_data[field_mapping["name"]] = self.ocr_result["name"]["text"]
            qty_text = self.ocr_result["qty"]["text"].replace(",", "")
            table_data[field_mapping["qty"]] = int(qty_text) if qty_text.isdigit() else qty_text
            table_data[field_mapping["batch"]] = self.ocr_result["batch"]["text"]
            
            # 处理日期
            date_text = self.ocr_result["date"]["text"].replace(",", ".").strip()
            if date_text:
                try:
                    date_obj = datetime.strptime(date_text, "%Y.%m.%d")
                    timestamp = int(date_obj.timestamp() * 1000)
                    table_data[field_mapping["date"]] = str(timestamp)
                except:
                    table_data[field_mapping["date"]] = date_text
            else:
                table_data[field_mapping["date"]] = ""

            # 构建请求体
            request_body = {
                "add_records": [
                    {
                        "values": table_data
                    }
                ]
            }

            # 发送请求
            response = requests.post(
                url=WEWORK_CONFIG["webhook_url"],
                data=json.dumps(request_body, ensure_ascii=False),
                headers=WEWORK_CONFIG["headers"],
                timeout=15
            )

            # 解析响应
            result = response.json()
            if result.get("errcode") == WEWORK_CONFIG["success_code"]:
                self.show_dialog(WEWORK_CONFIG["success_msg"])
                self.reset_interface()
            else:
                err_msg = result.get("errmsg", "Unknown error")
                self.show_dialog(f"提交失败: {err_msg} (code: {result.get('errcode')})")

        except requests.exceptions.Timeout:
            self.show_dialog("请求超时，请检查网络.")
        except requests.exceptions.ConnectionError:
            self.show_dialog("连接失败，请检查Webhook地址.")
        except Exception as e:
            self.show_dialog(f"提交错误: {str(e)}")

    # 重置界面
    def reset_interface(self):
        if self.preview_layout:
            self.root.remove_widget(self.preview_layout)
        self.root.ids.btn_container.opacity = 1
        self.ocr_result = {
            "no": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0},
            "name": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0},
            "qty": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0},
            "batch": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0},
            "date": {"text":"", "x":0, "y":0, "corrected_x":0, "corrected_y":0}
        }
        self.correction_ready = False

    # 显示弹窗
    def show_dialog(self, text):
        if self.dialog:
            self.dialog.dismiss()
        self.dialog = MDDialog(
            text=text,
            buttons=[MDFlatButton(text="确定", on_press=lambda x: self.dialog.dismiss(), font_name='Chinese')]
        )
        self.dialog.open()

if __name__ == "__main__":
    ReceiptApp().run()