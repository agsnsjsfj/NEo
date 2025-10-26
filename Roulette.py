#This is released by a file by BBBBYB2 :: Syyad
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ChatMember
import uuid
import re
import random
import threading
import time
from datetime import datetime, timedelta
import pytz

class RouletteBot:
    API_TOKEN = '8302358085:AAGtsRt7oblV4xb69fP72opqoxFMUm8nyeo'
    ADMIN_ID = 8177065892

    def __init__(self):
        self.bot = telebot.TeleBot(self.API_TOKEN)
        self.user_states = {}
        self.user_temp_data = {}
        self.user_bound_channels = {}
        self.active_roulettes = {}
        self.banned_from_creator_roulettes = {}
        self.global_forced_channels = {}
        self.baghdad_tz = pytz.timezone('Asia/Baghdad')

        self.bot_active = True
        self.total_users_count = 0
        self.known_users = set()

        self.ROULETTE_TEXT_PROMPT = (
            "أرسل كليشة السحب\n\n"
            "1 - للتشويش: <code>&lt;tg-spoiler&gt;&lt;/tg-spoiler&gt;</code>\n"
            "<tg-spoiler>مثال</tg-spoiler>\n\n"
            "2 - للتعريض: <code>&lt;b&gt;&lt;/b&gt;</code>\n"
            "<b>مثال</b>\n\n"
            "3 - لجعل النص مائل: <code>&lt;i&gt;&lt;/i&gt;</code>\n"
            "<i>مثال</i>\n\n"
            "4 - للاقتباس: <code>&lt;blockquote&gt;&lt;/blockquote&gt;</code>\n"
            "<blockquote>مثال</blockquote>\n\n"
            "رجاءً عدم إرسال روابط نهائياً 🚫⛔"
        )

        self.CHANNEL_BINDING_INSTRUCTIONS = (
            "1️⃣ أضف البوت كمشرف في قناتك.\n"
            "2️⃣ قم بإعادة توجيه أي رسالة من قناتك إلى البوت.\n\n"
            "📌 ملاحظة:\n"
            "جميع المشرفين الآخرين في القناة سيتمكنون أيضًا من استخدام البوت بعد إضافته."
        )

        self.CONDITIONAL_CHANNEL_QUESTION = "هل تريد إضافة قناة شرط؟\n\nعند إضافة قناة شرط لن يتمكن أحد من المشاركة في السحب قبل الانضمام لقناة الشرط."
        self.SEND_CONDITIONAL_CHANNEL_LINK = "أرسل رابط القناة الشرطية (مثال: @YourChannel / https://t.me/YourChannel)"

        self.NOT_YOUR_COMMAND_MSG = "هذا الأمر مخصص لمنشئ الروليت فقط. ❗"
        self.BOT_MAINTENANCE_MSG = "البوت متوقف حالياً للصيانة."
        self.FORCED_CHANNEL_PROMPT_MSG = "عليك الانضمام إلى القنوات الإجبارية التالية للمتابعة:"

        self.ROULETTE_TYPE_TEXT_NORMAL = "الروليت العادي: سحب مجاني بدون شروط خاصة"
        self.ROULETTE_TYPE_TEXT_PROTECTED = "الروليت المحمي: سحب محمي ضد الرشق"

        self.DRAW_METHOD_TEXT_MANUAL = "• سحب يدوي: تحكم كامل في توقيت السحب من ادوس بدء روليت يبدء"
        self.DRAW_METHOD_TEXT_AUTOMATIC = "• سحب تلقائي: سحب آلي بعد انتهاء المدة "

        self.register_handlers()

    def main_menu_kb(self, user_id):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("بدء روليت 🎲", callback_data="start_roulette_select_channel_prompt"))
        kb.add(InlineKeyboardButton("قنواتي ➕", callback_data="my_channels_menu"),
               InlineKeyboardButton("ذكرني إذا فزت 🔔", callback_data="remind_me_global_info"))
        kb.add(InlineKeyboardButton("مطور البوت", url="https://t.me/t_716"), InlineKeyboardButton("قنا البوت", url="https://t.me/Vyw6bot"))
        kb.add(InlineKeyboardButton("المساعدة", callback_data="show_help_info"))
        if user_id == self.ADMIN_ID:
            kb.add(InlineKeyboardButton("لوحة الأدمن ⚙️", callback_data="admin_panel"))
        return kb

    def admin_panel_kb(self):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("عرض الإحصائيات 📊", callback_data="show_bot_stats"))
        kb.add(InlineKeyboardButton("إضافة قناة اشتراك إجباري ➕", callback_data="add_global_forced_channel_prompt"))
        kb.add(InlineKeyboardButton("إزالة قناة اشتراك إجباري 🗑️", callback_data="remove_global_forced_channel_prompt"))
        if self.bot_active:
            kb.add(InlineKeyboardButton("إيقاف البوت 🔴", callback_data="stop_bot_for_maintenance"))
        else:
            kb.add(InlineKeyboardButton("تشغيل البوت 🟢", callback_data="start_bot_from_maintenance"))
        kb.add(InlineKeyboardButton("رجوع للقائمة الرئيسية 🔙", callback_data="back_to_main_menu"))
        return kb

    @staticmethod
    def my_channels_kb():
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("إضافة قناة ➕", callback_data="add_channel_prompt"))
        kb.add(InlineKeyboardButton("عرض قنواتي 📝", callback_data="view_my_channels"))
        kb.add(InlineKeyboardButton("حذف قناة 🗑️", callback_data="delete_channel_prompt"))
        kb.add(InlineKeyboardButton("رجوع 🔙", callback_data="back_to_main_menu"))
        return kb

    @staticmethod
    def roulette_type_selection_kb():
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("الروليت العادي", callback_data="select_roulette_type_normal"))
        kb.add(InlineKeyboardButton("الروليت المحمي", callback_data="select_roulette_type_protected"))
        kb.add(InlineKeyboardButton("رجوع 🔙", callback_data="start_roulette_select_channel_prompt"))
        return kb

    @staticmethod
    def draw_method_selection_kb():
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("سحب يدوي", callback_data="select_draw_method_manual"))
        kb.add(InlineKeyboardButton("سحب تلقائي", callback_data="select_draw_method_automatic"))
        kb.add(InlineKeyboardButton("رجوع 🔙", callback_data="select_roulette_type_prompt"))
        return kb

    @staticmethod
    def auto_draw_duration_unit_kb():
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("بالدقائق", callback_data="auto_draw_unit_minutes"))
        kb.add(InlineKeyboardButton("بالساعات", callback_data="auto_draw_unit_hours"))
        kb.add(InlineKeyboardButton("بالأيام", callback_data="auto_draw_unit_days"))
        kb.add(InlineKeyboardButton("رجوع 🔙", callback_data="select_draw_method_prompt"))
        return kb

    @staticmethod
    def roulette_creation_options_kb():
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("تعديل الكليشة 🎨", callback_data="choose_style_instructions"))
        kb.add(InlineKeyboardButton("إضافة قناة شرط ➕", callback_data="prompt_conditional_channel"))
        kb.add(InlineKeyboardButton("تخطي ⏭️", callback_data="skip_conditional_channel"))
        return kb

    @staticmethod
    def conditional_channel_choice_kb():
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("إضافة رابط قناة 🔗", callback_data="send_conditional_channel_link_prompt"))
        kb.add(InlineKeyboardButton("تخطي ⏭️", callback_data="skip_conditional_channel"))
        kb.add(InlineKeyboardButton("رجوع 🔙", callback_data="back_to_roulette_creation_options"))
        return kb

    def get_channel_roulette_markup(self, roulette_id: str, is_active: bool, is_draw_manual: bool):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("المشاركة في السحب 🎁", callback_data=f"join_roulette_{roulette_id}"))
        kb.add(InlineKeyboardButton("ذكرني إذا فزت 🔔", callback_data=f"remind_me_roulette_{roulette_id}"))

        r = self.active_roulettes.get(roulette_id)

        if r and is_draw_manual and not r.get('final_winners_determined', False):
            if r['active']:
                kb.add(InlineKeyboardButton("إيقاف المشاركة ⏸️", callback_data=f"toggle_participation_{roulette_id}"))
            else:
                kb.add(InlineKeyboardButton("تشغيل المشاركة ▶️", callback_data=f"toggle_participation_{roulette_id}"))

            if len(r['participants']) > 0:
                if r.get('draw_started_manually', False) and len(r.get('current_draw_pool', [])) > r['winners_count']:
                    kb.add(InlineKeyboardButton("استبعاد مشارك آخر", callback_data=f"start_draw_{roulette_id}"))
                elif not r.get('draw_started_manually', False) and len(r['participants']) > r['winners_count']:
                    kb.add(InlineKeyboardButton("ابدأ السحب 🏁", callback_data=f"start_draw_{roulette_id}"))

        kb.add(InlineKeyboardButton("عرض المشاركين 📊", callback_data=f"view_participants_{roulette_id}"))
        return kb

    @staticmethod
    def creator_exclude_kb(roulette_id: str, participant_id: int):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("استبعاد هذا المشارك ❌", callback_data=f"exclude_participant_{roulette_id}_{participant_id}"))
        return kb

    def _is_channel_member(self, channel_id, user_id):
        try:
            member = self.bot.get_chat_member(channel_id, user_id)
            return member.status not in ['left', 'kicked']
        except Exception:
            return False
#This is released by a file by BBBBYB2 :: Syyad
    def _is_channel_admin_or_owner(self, channel_id, user_id):
        try:
            member = self.bot.get_chat_member(channel_id, user_id)
            return member.status in ['administrator', 'creator']
        except Exception:
            return False

    @staticmethod
    def _get_channel_info_from_link(link: str):
        match_username = re.match(r"^(?:https?://t\.me/)?@?([a-zA-Z0-9_]+)$", link)
        if match_username:
            return "@" + match_username.group(1)
        return None

    def _update_roulette_message(self, roulette_id: str):
        r = self.active_roulettes.get(roulette_id)
        if not r:
            return

        try:
            initial_participants_count = len(r['participants'])
            current_draw_pool_count = len(r['current_draw_pool']) if r.get('current_draw_pool') else 0

            if r['main_channel_username']:
                channel_display = f"<a href='https://t.me/{r['main_channel_username']}'>{r['main_channel_title']}</a>"
            else:
                channel_display = f"\"{r['main_channel_title']}\""
            header_text = f"بدءَ روليت في قناة {channel_display} 🗯️"
            updated_text = f"{header_text}\n\n{r['text']}"

            if r.get('final_winners_determined', False):
                winners_usernames = []
                for winner_id in r['winners']:
                    try:
                        winner_info = self.bot.get_chat(winner_id)
                        winners_usernames.append(f"<a href='tg://user?id={winner_id}'>{winner_info.first_name or winner_info.username or f'المستخدم {winner_id}'}</a>")
                    except Exception:
                        winners_usernames.append(f"<a href='tg://user?id={winner_id}'>المستخدم {winner_id}</a>")
                updated_text += "\n\nالفائزون بالروليت 🥇:\n" + "\n".join(winners_usernames)
            elif r.get('draw_started_manually', False) or r['draw_method'] == 'automatic':
                updated_text += f"\n\nعدد المشاركين في الروليت : \"{current_draw_pool_count}\" 🕹️"
                if len(r.get('current_draw_pool', [])) > r['winners_count']:
                    if r.get('last_eliminated') is not None:
                        try:
                            eliminated_info = self.bot.get_chat(r['last_eliminated'])
                            eliminated_name = eliminated_info.first_name if eliminated_info.first_name else f"المستخدم {r['last_eliminated']}"
                            updated_text += f"\n\nآخر مستبعد : <a href='tg://user?id={r['last_eliminated']}'>{eliminated_name}</a>"
                        except Exception:
                            updated_text += f"\n\nآخر مستبعد : <a href='tg://user?id={r['last_eliminated']}'>المستخدم {r['last_eliminated']}</a>"
                    updated_text += f"\nالمتبقون: {len(r['current_draw_pool'])}"
                elif len(r.get('current_draw_pool', [])) == r['winners_count'] and r['winners_count'] > 0:
                    r['winners'] = list(r['current_draw_pool'])
                    r['final_winners_determined'] = True
                    r['active'] = False
                    winners_usernames = []
                    for winner_id in r['winners']:
                        try:
                            winner_info = self.bot.get_chat(winner_id)
                            winners_usernames.append(f"<a href='tg://user?id={winner_id}'>{winner_info.first_name or winner_info.username or f'المستخدم {winner_id}'}</a>")
                        except Exception:
                            winners_usernames.append(f"<a href='tg://user?id={winner_id}'>المستخدم {winner_id}</a>")
                    updated_text += "\n\nالفائزون بالروليت 🥇:\n" + "\n".join(winners_usernames)
            else:
                updated_text += f"\n\nعدد المشاركين في الروليت : \"{initial_participants_count}\" 🕹️"
                updated_text += "\n\nحالة السحب : لم يبدأ بعد.⏳"

            if not r['active'] and not r.get('final_winners_determined', False) and not r.get('draw_started_manually', False):
                updated_text += "\nالمشاركة متوقفة حالياً. ⛔"

            if r['draw_method'] == 'automatic' and not r.get('final_winners_determined', False):
                draw_time = datetime.fromtimestamp(r['draw_time_unix'], tz=pytz.utc).astimezone(self.baghdad_tz)
                updated_text += f"\nموعد السحب النهائي ⏰: {draw_time.strftime('%Y-%m-%d %H:%M:%S')}"
                if r['active'] and r.get('draw_started_manually', False):
                    updated_text += "\nالسحب التلقائي قيد التقدم... 🔁"

            self.bot.edit_message_text(
                chat_id=r['main_channel_id'],
                message_id=r['channel_message_id'],
                text=updated_text,
                parse_mode="HTML",
                reply_markup=self.get_channel_roulette_markup(roulette_id, r['active'], r['draw_method'] == 'manual')
            )
        except Exception:
            pass

    def _perform_draw(self, roulette_id: str):
        r = self.active_roulettes.get(roulette_id)
        if not r:
            return

        if r['final_winners_determined']:
            return

        if not r.get('current_draw_pool'):
            r['current_draw_pool'] = set(r['participants'])
            r['last_eliminated'] = None

        if len(r['current_draw_pool']) <= r['winners_count']:
            r['winners'] = list(r['current_draw_pool'])
            r['final_winners_determined'] = True
            r['active'] = False
            self._update_roulette_message(roulette_id)

            try:
                self.bot.send_message(r['creator_id'], "تم تحديد الفائزين النهائيين! ✅🎉")
            except Exception:
                pass

            for winner_id in r['winners']:
                if winner_id in r['reminders']:
                    try:
                        winner_info = self.bot.get_chat(winner_id)
                        self.bot.send_message(
                            winner_id,
                            f"تهانينا! لقد فزت في السحب! 🎉\n\n{r['text']}\n\nيمكنك التحقق من الفائزين في القناة: <a href='https://t.me/{r['main_channel_username']}'>{r['main_channel_title']}</a> 🏆",
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass
            return

        eliminated_id = random.choice(list(r['current_draw_pool']))
        r['current_draw_pool'].discard(eliminated_id)
        r['last_eliminated'] = eliminated_id

        self._update_roulette_message(roulette_id)

        try:
            eliminated_info = self.bot.get_chat(eliminated_id)
            eliminated_name = eliminated_info.first_name if eliminated_info.first_name else f"المستخدم {eliminated_id}"
            self.bot.send_message(r['creator_id'], f"تم استبعاد: <a href='tg://user?id={eliminated_id}'>{eliminated_name}</a> 🔄\nالمتبقون: {len(r['current_draw_pool'])}", parse_mode="HTML")
        except Exception:
            pass

        if r['draw_method'] == 'automatic' and not r['final_winners_determined']:
            timer = threading.Timer(5, self._perform_draw, args=[roulette_id])
            timer.start()
            self.active_roulettes[roulette_id]['auto_draw_timer'] = timer

    def _publish_roulette(self, user_id: int):
        data = self.user_temp_data.get(user_id)
        if not data or 'roulette_text' not in data or 'main_channel_id' not in data or 'winners_count' not in data or 'draw_method' not in data:
            self.bot.send_message(user_id, "حدث خطأ: بيانات الروليت غير مكتملة. يرجى البدء من جديد عبر /start. ❗")
            return

        roulette_id = str(uuid.uuid4())

        if data['main_channel_username']:
            channel_display = f"<a href='https://t.me/{data['main_channel_username']}'>{data['main_channel_title']}</a>"
        else:
            channel_display = f"\"{data['main_channel_title']}\""
        header_text = f"بدءَ روليت في قناة {channel_display} 🗯️"
        initial_text = f"{header_text}\n\n{data['roulette_text']}\n\nعدد المشاركين في الروليت : \"0\" 🕹️\n\nحالة السحب : لم يبدأ بعد.⏳"

        if data['draw_method'] == 'automatic':
            draw_time_utc = datetime.fromtimestamp(data['draw_time_unix'], tz=pytz.utc)
            draw_time_baghdad = draw_time_utc.astimezone(self.baghdad_tz)
            initial_text += f"\nموعد السحب النهائي ⏰: {draw_time_baghdad.strftime('%Y-%m-%d %H:%M:%S')} "

        try:
            channel_message = self.bot.send_message(
                chat_id=data['main_channel_id'],
                text=initial_text,
                parse_mode="HTML",
                reply_markup=self.get_channel_roulette_markup(roulette_id, True, data['draw_method'] == 'manual')
            )

            self.active_roulettes[roulette_id] = {
                'creator_id': user_id,
                'main_channel_id': data['main_channel_id'],
                'main_channel_username': data['main_channel_username'],
                'main_channel_title': data['main_channel_title'],
                'channel_message_id': channel_message.message_id,
                'text': data['roulette_text'],
                'conditional_channel_id': data.get('conditional_channel_id'),
                'conditional_channel_username': data.get('conditional_channel_username'),
                'winners_count': data['winners_count'],
                'participants': set(),
                'current_draw_pool': set(),
                'active': True,
                'draw_started_manually': False,
                'winners': [],
                'last_eliminated': None,
                'final_winners_determined': False,
                'reminders': set(),
                'roulette_type': data['roulette_type'],
                'draw_method': data['draw_method'],
                'draw_time_unix': data.get('draw_time_unix'),
                'auto_draw_timer': None
            }

            if data['draw_method'] == 'automatic':
                delay = data['draw_time_unix'] - time.time()
                if delay < 0:
                    delay = 1
                    self.bot.send_message(user_id, "موعد السحب التلقائي كان في الماضي، سيتم بدء السحب تلقائياً بعد لحظات. ⚠️")
                timer = threading.Timer(delay, self._start_automatic_draw_process, args=[roulette_id])
                timer.start()
                self.active_roulettes[roulette_id]['auto_draw_timer'] = timer

            self.bot.send_message(
                user_id,
                f"تم نشر الروليت في القناة: @{data['main_channel_username']} ✅\n\nتحكم بالروليت الخاص بك من خلال رسالة السحب في القناة (ID: {roulette_id})."
            )
            self.bot.send_message(user_id, "تم إنشاء الروليت بنجاح ونشره! 🎉")

        except telebot.apihelper.ApiTelegramException as e:
            self.bot.send_message(user_id, f"فشل في النشر داخل القناة. تأكد أن البوت مشرف ولديه صلاحية إرسال الرسائل. ❗\nالخطأ: {e}")
            self.active_roulettes.pop(roulette_id, None)
        except Exception as e:
            self.bot.send_message(user_id, f"حدث خطأ غير متوقع أثناء نشر الروليت: {e} ❗")
            self.active_roulettes.pop(roulette_id, None)

    def _start_automatic_draw_process(self, roulette_id: str):
        r = self.active_roulettes.get(roulette_id)
        if not r:
            return

        if not r['participants']:
            try:
                self.bot.send_message(r['creator_id'], "السحب التلقائي لم يبدأ: لا يوجد مشاركون. ❗🚫")
            except Exception:
                pass
            r['active'] = False
            r['final_winners_determined'] = True
            self._update_roulette_message(roulette_id)
            return

        r['draw_started_manually'] = True
        r['active'] = False
        r['current_draw_pool'] = set(r['participants'])
        self._update_roulette_message(roulette_id)
        try:
            self.bot.send_message(r['creator_id'], "بدأ السحب التلقائي الآن! ✅🏁")
        except Exception:
            pass
        self._perform_draw(roulette_id)

    def _check_bot_status(self, message):
        if not self.bot_active and message.from_user.id != self.ADMIN_ID:
            self.bot.send_message(message.chat.id, self.BOT_MAINTENANCE_MSG)
            return False
        return True

    def _check_bot_status_callback(self, call):
        if not self.bot_active and call.from_user.id != self.ADMIN_ID:
            self.bot.answer_callback_query(call.id, self.BOT_MAINTENANCE_MSG, show_alert=True)
            return False
        return True
    
    def _check_global_forced_subscription_message(self, message: Message):
        user_id = message.from_user.id
        if not self.global_forced_channels:
            return True

        missing_channels_info = []
        for cid, c_info in self.global_forced_channels.items():
            if not self._is_channel_member(cid, user_id):
                link_to_send = f"https://t.me/{c_info['username']}" if c_info['username'] else f"{c_info['title']}"
                missing_channels_info.append(link_to_send)
        
        if missing_channels_info:
            message_text = f"{self.FORCED_CHANNEL_PROMPT_MSG}\n" + "\n".join(missing_channels_info)
            self.bot.send_message(user_id, message_text, parse_mode="HTML")
            return False
        return True
#This is released by a file by BBBBYB2 :: Syyad
    def _check_global_forced_subscription_callback(self, call):
        user_id = call.from_user.id
        if not self.global_forced_channels:
            return True

        missing_channels_info = []
        for cid, c_info in self.global_forced_channels.items():
            if not self._is_channel_member(cid, user_id):
                link_to_send = f"https://t.me/{c_info['username']}" if c_info['username'] else f"{c_info['title']}"
                missing_channels_info.append(link_to_send)
        
        if missing_channels_info:
            message_text = f"{self.FORCED_CHANNEL_PROMPT_MSG}\n" + "\n".join(missing_channels_info)
            self.bot.answer_callback_query(call.id, "عليك الاشتراك في القنوات الإجبارية. ⚠️", show_alert=True)
            self.bot.send_message(user_id, message_text, parse_mode="HTML")
            return False
        return True

    def register_handlers(self):
        self.bot.message_handler(commands=['start'])(self.start_cmd)
        self.bot.callback_query_handler(func=lambda c: c.data == "back_to_main_menu")(self.handle_back_to_main_menu)
        self.bot.callback_query_handler(func=lambda c: c.data == "my_channels_menu")(self.handle_my_channels_menu)
        self.bot.callback_query_handler(func=lambda c: c.data == "add_channel_prompt")(self.handle_add_channel_prompt)
        self.bot.callback_query_handler(func=lambda c: c.data == "view_my_channels")(self.handle_view_my_channels)
        self.bot.callback_query_handler(func=lambda c: c.data == "delete_channel_prompt")(self.handle_delete_channel_prompt)
        self.bot.callback_query_handler(func=lambda c: c.data.startswith("delete_channel__"))(self.handle_delete_channel_selection)
        self.bot.callback_query_handler(func=lambda c: c.data == "start_roulette_select_channel_prompt")(self.handle_start_roulette_select_channel_prompt)
        self.bot.callback_query_handler(func=lambda c: c.data.startswith("select_roulette_channel__"))(self.handle_select_roulette_channel)
        self.bot.callback_query_handler(func=lambda c: c.data == "select_roulette_type_prompt")(self.handle_select_roulette_type_prompt_back)
        self.bot.callback_query_handler(func=lambda c: c.data.startswith("select_roulette_type_"))(self.handle_select_roulette_type)
        self.bot.callback_query_handler(func=lambda c: c.data == "select_draw_method_prompt")(self.handle_select_draw_method_prompt_back)
        self.bot.callback_query_handler(func=lambda c: c.data.startswith("select_draw_method_"))(self.handle_select_draw_method)
        self.bot.callback_query_handler(func=lambda c: c.data.startswith("auto_draw_unit_"))(self.handle_auto_draw_unit)
        self.bot.callback_query_handler(func=lambda c: c.data == "choose_style_instructions")(self.handle_choose_style_instructions)
        self.bot.callback_query_handler(func=lambda c: c.data == "prompt_conditional_channel")(self.handle_prompt_conditional_channel)
        self.bot.callback_query_handler(func=lambda c: c.data == "back_to_roulette_creation_options")(self.handle_back_to_roulette_creation_options)
        self.bot.callback_query_handler(func=lambda c: c.data == "send_conditional_channel_link_prompt")(self.handle_send_conditional_channel_link_prompt)
        self.bot.callback_query_handler(func=lambda c: c.data == "skip_conditional_channel")(self.handle_skip_conditional_channel)
        self.bot.callback_query_handler(func=lambda c: c.data.startswith("join_roulette_"))(self.handle_join_roulette)
        self.bot.callback_query_handler(func=lambda c: c.data.startswith("toggle_participation_"))(self.handle_toggle_participation)
        self.bot.callback_query_handler(func=lambda c: c.data.startswith("start_draw_"))(self.handle_start_draw)
        self.bot.callback_query_handler(func=lambda c: c.data.startswith("exclude_participant_"))(self.handle_exclude_participant)
        self.bot.callback_query_handler(func=lambda c: c.data.startswith("remind_me_roulette_"))(self.handle_remind_me_roulette)
        self.bot.callback_query_handler(func=lambda c: c.data == "remind_me_global_info")(self.handle_remind_me_global_info)
        self.bot.callback_query_handler(func=lambda c: c.data.startswith("view_participants_"))(self.handle_view_participants)
        self.bot.callback_query_handler(func=lambda c: c.data == "show_help_info")(self.handle_show_help_info)

        self.bot.callback_query_handler(func=lambda c: c.data == "admin_panel")(self.handle_admin_panel)
        self.bot.callback_query_handler(func=lambda c: c.data == "show_bot_stats")(self.handle_show_bot_stats)
        self.bot.callback_query_handler(func=lambda c: c.data == "add_global_forced_channel_prompt")(self.handle_add_global_forced_channel_prompt)
        self.bot.callback_query_handler(func=lambda c: c.data == "remove_global_forced_channel_prompt")(self.handle_remove_global_forced_channel_prompt)
        self.bot.callback_query_handler(func=lambda c: c.data.startswith("remove_global_channel__"))(self.handle_remove_global_channel_selection)
        self.bot.callback_query_handler(func=lambda c: c.data == "stop_bot_for_maintenance")(self.handle_stop_bot_for_maintenance)
        self.bot.callback_query_handler(func=lambda c: c.data == "start_bot_from_maintenance")(self.handle_start_bot_from_maintenance)

        self.bot.message_handler(content_types=['text', 'audio', 'photo', 'video', 'document'], func=lambda message: True)(self.handle_messages_by_state)

    def start_cmd(self, message: Message):
        user_id = message.from_user.id
        if not self._check_bot_status(message):
            return
        
        if not self._check_global_forced_subscription_message(message):
            return

        if user_id not in self.known_users:
            self.known_users.add(user_id)
            self.total_users_count += 1
            user_full_name = message.from_user.full_name or message.from_user.first_name or "غير معروف"
            user_username = message.from_user.username if message.from_user.username else "لا يوجد"
            try:
                self.bot.send_message(
                    self.ADMIN_ID,
                    f"دخول مستخدم جديد للبوت! 🔔\n"
                    f"الاسم: {user_full_name}\n"
                    f"المعرف: @{user_username}\n"
                    f"الآيدي: `{user_id}`\n"
                    f"العدد الكلي للمستخدمين: {self.total_users_count}",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

        self.user_states.pop(user_id, None)
        self.user_temp_data.pop(user_id, None)

        user_full_name_fallback = message.from_user.full_name or message.from_user.first_name or "صديقي"

        welcome_message_parts = []
        welcome_message_parts.append("اهلا بكم في روليت الجرف 👋\n\n")
        welcome_part = f"أهلاً بك <a href='tg://user?id={user_id}'>{user_full_name_fallback}</a>"
        welcome_message_parts.append(welcome_part)
        welcome_message_parts.append("، يسرني وجودك هنا! 😊\n\n")
        welcome_message_parts.append("هذا البوت يتيح لك تنظيم سحوبات وروليتات بسهولة وفعالية في قنواتك، مع خيارات متعددة لتلبية احتياجاتك. ✨")
        welcome_message_parts.append("سواء كنت ترغب في سحب يدوي أو تلقائي، أو حتى سحب محمي، كل ذلك متاح لك.\n\n")
        welcome_message_parts.append("ابدأ الآن بتحديد القناة التي تود إجراء السحب فيها، أو قم بإدارة قنواتك المضافة. ⚙️")
        welcome_message_text = "".join(welcome_message_parts)

        self.bot.send_message(
            message.chat.id,
            welcome_message_text,
            reply_markup=self.main_menu_kb(user_id),
            parse_mode="HTML"
        )

    def handle_back_to_main_menu(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
#This is released by a file by BBBBYB2 :: Syyad
        user_id = call.from_user.id
        self.user_states.pop(user_id, None)
        self.user_temp_data.pop(user_id, None)
        self.bot.answer_callback_query(call.id)

        user_full_name_fallback = call.from_user.full_name or call.from_user.first_name or "صديقي"
        user_username = call.from_user.username

        welcome_message_parts = []
        welcome_message_parts.append("اهلا بكم في روليت الجرف 👋\n\n")
        welcome_part = f"أهلاً بك <a href='tg://user?id={user_id}'>{user_full_name_fallback}</a>"
        if user_username:
            welcome_part += f" (@{user_username})"
        welcome_message_parts.append(welcome_part)
        welcome_message_parts.append("، يسرني وجودك هنا! 😊\n\n")
        welcome_message_parts.append("هذا البوت يتيح لك تنظيم سحوبات وروليتات بسهولة وفعالية في قنواتك، مع خيارات متعددة لتلبية احتياجاتك. ✨")
        welcome_message_parts.append("سواء كنت ترغب في سحب يدوي أو تلقائي، أو حتى سحب محمي، كل ذلك متاح لك.\n\n")
        welcome_message_parts.append("ابدأ الآن بتحديد القناة التي تود إجراء السحب فيها، أو قم بإدارة قنواتك المضافة. ⚙️")
        welcome_message_text = "".join(welcome_message_parts)

        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=welcome_message_text,
            reply_markup=self.main_menu_kb(user_id),
            parse_mode="HTML"
        )

    def handle_my_channels_menu(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        self.bot.answer_callback_query(call.id)
        self.user_states[user_id] = 'my_channels_menu'
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="إدارة قنواتك:",
            reply_markup=self.my_channels_kb()
        )

    def handle_add_channel_prompt(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        self.bot.answer_callback_query(call.id)
        self.bot.send_message(call.message.chat.id, self.CHANNEL_BINDING_INSTRUCTIONS)
        self.user_states[user_id] = 'awaiting_channel_to_add_forward'

    def handle_view_my_channels(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        self.bot.answer_callback_query(call.id)
        channels = self.user_bound_channels.get(user_id)
        if not channels:
            self.bot.send_message(call.message.chat.id, "لم تقم بإضافة أي قنوات بعد. ❗❌")
            return

        channel_list_text = "قنواتك المضافة:\n"
        for cid, c_info in channels.items():
            channel_list_text += f"- {c_info.get('title', 'غير معروف')} (@{c_info.get('username', 'لا يوجد')})\n"
        self.bot.send_message(call.message.chat.id, channel_list_text)

    def handle_delete_channel_prompt(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        self.bot.answer_callback_query(call.id)
        channels = self.user_bound_channels.get(user_id)
        if not channels:
            self.bot.send_message(call.message.chat.id, "لم تقم بإضافة أي قنوات لحذفها. ❗❌")
            return

        delete_kb = InlineKeyboardMarkup()
        for cid, c_info in channels.items():
            delete_kb.add(InlineKeyboardButton(f"{c_info.get('title', 'غير معروف')} 🗑️", callback_data=f"delete_channel__{cid}"))
        delete_kb.add(InlineKeyboardButton("رجوع 🔙", callback_data="my_channels_menu"))

        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="اختر القناة لحذفها:",
            reply_markup=delete_kb
        )
        self.user_states[user_id] = 'awaiting_channel_to_delete_selection'

    def handle_delete_channel_selection(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        channel_id_str = call.data.split("__")[1]
        channel_id = int(channel_id_str)
        self.bot.answer_callback_query(call.id)

        if user_id in self.user_bound_channels and channel_id in self.user_bound_channels[user_id]:
            channel_info = self.user_bound_channels[user_id].pop(channel_id)
            if not self.user_bound_channels[user_id]:
                self.user_bound_channels.pop(user_id)
            self.bot.send_message(call.message.chat.id, f"تم حذف القناة: {channel_info.get('title', 'غير معروف')}. ✅🗑️")
        else:
            self.bot.send_message(call.message.chat.id, "هذه القناة غير موجودة في قائمة قنواتك. ❗❌")

        self.handle_my_channels_menu(call)

    def handle_start_roulette_select_channel_prompt(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        self.bot.answer_callback_query(call.id)
        channels = self.user_bound_channels.get(user_id)
        if not channels:
            self.bot.send_message(call.message.chat.id, "عليك إضافة قناة أولاً في قسم 'قنواتي' قبل إنشاء روليت. ❗❌")
            return

        select_channel_kb = InlineKeyboardMarkup()
        for cid, c_info in channels.items():
            select_channel_kb.add(InlineKeyboardButton(f"{c_info.get('title', 'غير معروف')} (@{c_info.get('username', 'لا يوجد')})", callback_data=f"select_roulette_channel__{cid}"))
        select_channel_kb.add(InlineKeyboardButton("رجوع 🔙", callback_data="back_to_main_menu"))
#This is released by a file by BBBBYB2 :: Syyad
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="اختر القناة التي تريد نشر الروليت فيها:",
            reply_markup=select_channel_kb
        )
        self.user_states[user_id] = 'awaiting_roulette_channel_selection'

    def handle_select_roulette_channel(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        channel_id_str = call.data.split("__")[1]
        channel_id = int(channel_id_str)
        self.bot.answer_callback_query(call.id)

        if user_id not in self.user_bound_channels or channel_id not in self.user_bound_channels[user_id]:
            self.bot.send_message(call.message.chat.id, "القناة غير صالحة أو لم تعد مربوطة بحسابك. ❗❌")
            self.handle_start_roulette_select_channel_prompt(call)
            return

        selected_channel_info = self.user_bound_channels[user_id][channel_id]
        self.user_temp_data[user_id] = {
            'main_channel_id': channel_id,
            'main_channel_username': selected_channel_info['username'],
            'main_channel_title': selected_channel_info['title']
        }

        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"تم اختيار قناة: {selected_channel_info['title']}\n\nاختر نوع الروليت:\n{self.ROULETTE_TYPE_TEXT_NORMAL}\n{self.ROULETTE_TYPE_TEXT_PROTECTED}",
            reply_markup=self.roulette_type_selection_kb()
        )
        self.user_states[user_id] = 'awaiting_roulette_type_selection'

    def handle_select_roulette_type_prompt_back(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        self.bot.answer_callback_query(call.id)
        if 'main_channel_id' not in self.user_temp_data.get(user_id, {}):
            self.handle_start_roulette_select_channel_prompt(call)
            return

        selected_channel_info = self.user_bound_channels[user_id][self.user_temp_data[user_id]['main_channel_id']]
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"تم اختيار قناة: {selected_channel_info['title']}\n\nاختر نوع الروليت:\n{self.ROULETTE_TYPE_TEXT_NORMAL}\n{self.ROULETTE_TYPE_TEXT_PROTECTED}",
            reply_markup=self.roulette_type_selection_kb()
        )
        self.user_states[user_id] = 'awaiting_roulette_type_selection'

    def handle_select_roulette_type(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        roulette_type = call.data.split("_")[3]
        self.bot.answer_callback_query(call.id)

        if 'main_channel_id' not in self.user_temp_data.get(user_id, {}):
            self.bot.send_message(call.message.chat.id, "حدث خطأ، يرجى البدء من جديد. ❗❌")
            self.start_cmd(call.message)
            return

        self.user_temp_data[user_id]['roulette_type'] = roulette_type

        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"الخطوة التالية: نوع السحب\n\nاختر طريقة عمل السحب:\n{self.DRAW_METHOD_TEXT_MANUAL}\n{self.DRAW_METHOD_TEXT_AUTOMATIC}\n\nاختر الطريقة المناسبة لك",
            reply_markup=self.draw_method_selection_kb()
        )
        self.user_states[user_id] = 'awaiting_draw_method_selection'

    def handle_select_draw_method_prompt_back(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        self.bot.answer_callback_query(call.id)
        if 'main_channel_id' not in self.user_temp_data.get(user_id, {}):
            self.handle_start_roulette_select_channel_prompt(call)
            return

        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"الخطوة التالية: نوع السحب\n\nاختر طريقة عمل السحب:\n{self.DRAW_METHOD_TEXT_MANUAL}\n{self.DRAW_METHOD_TEXT_AUTOMATIC}\n\nاختر الطريقة المناسبة لك",
            reply_markup=self.draw_method_selection_kb()
        )
        self.user_states[user_id] = 'awaiting_draw_method_selection'

    def handle_select_draw_method(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        draw_method = call.data.split("_")[3]
        self.bot.answer_callback_query(call.id)

        if 'main_channel_id' not in self.user_temp_data.get(user_id, {}):
            self.bot.send_message(call.message.chat.id, "حدث خطأ، يرجى البدء من جديد. ❗❌")
            self.start_cmd(call.message)
            return

        self.user_temp_data[user_id]['draw_method'] = draw_method

        if draw_method == 'manual':
            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=self.ROULETTE_TEXT_PROMPT,
                parse_mode="HTML"
            )
            self.user_states[user_id] = 'awaiting_roulette_text'
        else:
            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="اختر وحدة المدة الزمنية للسحب التلقائي:",
                reply_markup=self.auto_draw_duration_unit_kb()
            )
            self.user_states[user_id] = 'awaiting_auto_draw_unit_selection'

    def handle_auto_draw_unit(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        unit = call.data.split("_")[3]
        self.bot.answer_callback_query(call.id)

        self.user_temp_data[user_id]['auto_draw_unit'] = unit
        self.bot.send_message(call.message.chat.id, f"أرسل المدة الزمنية بالعدد الذي اخترته ({unit}):")
        self.user_states[user_id] = 'awaiting_auto_draw_value'

    def handle_choose_style_instructions(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        if self.user_states.get(user_id) not in ['awaiting_roulette_options_choice', 'awaiting_roulette_text_edit_final']:
            self.bot.answer_callback_query(call.id, "لا يوجد كليشة سحب حالية لتعديلها. ❗❌", show_alert=True)
            return
        self.bot.answer_callback_query(call.id)
        self.bot.send_message(call.message.chat.id, self.ROULETTE_TEXT_PROMPT, parse_mode="HTML")
        self.user_states[user_id] = 'awaiting_roulette_text_edit'

    def handle_prompt_conditional_channel(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        if 'roulette_text' not in self.user_temp_data.get(user_id, {}):
            self.bot.answer_callback_query(call.id, "الرجاء إدخال كليشة السحب أولاً. ❗❌", show_alert=True)
            return
        self.bot.answer_callback_query(call.id)
        self.bot.send_message(call.message.chat.id, self.CONDITIONAL_CHANNEL_QUESTION, reply_markup=self.conditional_channel_choice_kb())
        self.user_states[user_id] = 'awaiting_conditional_channel_choice'

    def handle_back_to_roulette_creation_options(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        self.bot.answer_callback_query(call.id)
        if 'roulette_text' not in self.user_temp_data.get(user_id, {}):
            self.bot.send_message(call.message.chat.id, "حدث خطأ، يرجى البدء من جديد. ❗❌")
            self.start_cmd(call.message)
            return
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="اختر أحد الخيارات:",
            reply_markup=self.roulette_creation_options_kb()
        )
        self.user_states[user_id] = 'awaiting_roulette_options_choice'

    def handle_send_conditional_channel_link_prompt(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        self.bot.answer_callback_query(call.id)
        self.bot.send_message(call.message.chat.id, self.SEND_CONDITIONAL_CHANNEL_LINK)
        self.user_states[user_id] = 'awaiting_conditional_channel_link'

    def handle_skip_conditional_channel(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        user_id = call.from_user.id
        self.bot.answer_callback_query(call.id)
        self.user_temp_data[user_id]['conditional_channel_id'] = None
        self.user_temp_data[user_id]['conditional_channel_username'] = None
        self.bot.send_message(call.message.chat.id, "كم عدد الفائزين الذين تريد اختيارهم؟ 📝🔢\n(سيتوقف السحب حين يصل عدد المشاركين المتبقين لهذا العدد).")
        self.user_states[user_id] = 'awaiting_winner_count'
#This is released by a file by BBBBYB2 :: Syyad
    def handle_join_roulette(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        
        roulette_id = call.data.split("_")[2]
        user_id = call.from_user.id
        username = call.from_user.username
        first_name = call.from_user.first_name

        r = self.active_roulettes.get(roulette_id)
        if not r:
            self.bot.answer_callback_query(call.id, "السحب غير موجود. ❗❌", show_alert=True)
            return

        if user_id == r['creator_id']:
            if r.get('draw_started_manually', False):
                 self.bot.answer_callback_query(call.id, "لا يمكنك المشاركة في سحبك الخاص بعد بدء السحب. 🚫", show_alert=True)
                 return
            if r['draw_method'] == 'automatic' and r.get('draw_time_unix') and time.time() >= r['draw_time_unix']:
                 self.bot.answer_callback_query(call.id, "لا يمكنك المشاركة في سحبك الخاص بعد بدء السحب. 🚫", show_alert=True)
                 return

        if r.get('final_winners_determined', False):
            self.bot.answer_callback_query(call.id, "هذا السحب قد انتهى بالفعل وتم تحديد الفائزين. ⛔🛑", show_alert=True)
            return

        if not r['active']:
            self.bot.answer_callback_query(call.id, "المشاركة في هذا السحب متوقفة حالياً. ⛔🛑", show_alert=True)
            return

        if user_id in r['participants']:
            self.bot.answer_callback_query(call.id, "أنت مشارك بالفعل. ✅✔️", show_alert=True)
            return

        if r['roulette_type'] == 'protected' and user_id in self.banned_from_creator_roulettes.get(r['creator_id'], set()):
            self.bot.answer_callback_query(call.id, "تم استبعادك من سحوبات هذا المنشئ. 🚫⛔", show_alert=True)
            return

        if r['conditional_channel_id']:
            try:
                if not self._is_channel_member(r['conditional_channel_id'], user_id):
                    self.bot.answer_callback_query(call.id, "عليك الاشتراك بالقناة. ⚠️", show_alert=True)
                    conditional_channel_username = r.get('conditional_channel_username')
                    if conditional_channel_username:
                        link_to_send = f"https://t.me/{conditional_channel_username}"
                        self.bot.send_message(user_id, f"الرجاء الانضمام إلى القناة الشرطية للمشاركة في السحب:\n{link_to_send}")
                    return
            except Exception:
                self.bot.answer_callback_query(call.id, "خطأ في التحقق من الاشتراك في القناة الشرطية. ⚠️❗", show_alert=True)
                return

        r['participants'].add(user_id)
        if not r.get('draw_started_manually', False) and r['draw_method'] == 'manual':
            r['current_draw_pool'].add(user_id)

        self.bot.answer_callback_query(call.id, "تم تسجيل مشاركتك! ✅🥳")
        self._update_roulette_message(roulette_id)

        if r['roulette_type'] == 'protected':
            try:
                participant_name = first_name if first_name else "مجهول"
                participant_info_for_creator = f"👤 {participant_name}"
                if username:
                    participant_info_for_creator += f" (@{username})"
                participant_info_for_creator += f"\n?? {user_id}"

                self.bot.send_message(
                    r['creator_id'],
                    f"مشاركة جديدة في سحبك: ➕\n\nلقد شارك {participant_info_for_creator}\nعدد المشاركين الكلي: {len(r['participants'])} 📊",
                    reply_markup=self.creator_exclude_kb(roulette_id, user_id)
                )
            except Exception:
                pass
#This is released by a file by BBBBYB2 :: Syyad
    def handle_toggle_participation(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        roulette_id = call.data.split("_")[2]
        user_id = call.from_user.id
        r = self.active_roulettes.get(roulette_id)

        if not r or user_id != r['creator_id']:
            self.bot.answer_callback_query(call.id, self.NOT_YOUR_COMMAND_MSG, show_alert=True)
            return

        if r['draw_method'] == 'automatic':
            self.bot.answer_callback_query(call.id, "لا يمكن التحكم بالمشاركة في السحب التلقائي يدوياً. ❗🚫", show_alert=True)
            return

        if r.get('final_winners_determined', False):
            self.bot.answer_callback_query(call.id, "السحب قد انتهى ولا يمكن تغيير حالة المشاركة. ❗🚫", show_alert=True)
            return

        if r.get('draw_started_manually', False):
            self.bot.answer_callback_query(call.id, "لا يمكن إيقاف المشاركة بعد بدء السحب اليدوي. ❗🚫", show_alert=True)
            return

        self.bot.answer_callback_query(call.id)
        r['active'] = not r['active']
        status_text = "تم تشغيل المشاركة. ✅" if r['active'] else "تم إيقاف المشاركة. ⛔"
        self._update_roulette_message(roulette_id)
        self.bot.send_message(user_id, status_text)

    def handle_start_draw(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        roulette_id = call.data.split("_")[2]
        user_id = call.from_user.id
        r = self.active_roulettes.get(roulette_id)

        if not r or user_id != r['creator_id']:
            self.bot.answer_callback_query(call.id, self.NOT_YOUR_COMMAND_MSG, show_alert=True)
            return

        if r['draw_method'] == 'automatic':
            self.bot.answer_callback_query(call.id, "هذا السحب تلقائي وسيتم سحبه في الوقت المحدد. ❗🚫", show_alert=True)
            return

        if r.get('final_winners_determined', False):
            self.bot.answer_callback_query(call.id, "تم الانتهاء من هذا السحب مسبقاً. ❗🚫", show_alert=True)
            return

        if not r['participants'] and not r.get('draw_started_manually', False):
            self.bot.answer_callback_query(call.id, "لا يوجد مشاركون في السحب لبدء الاستبعاد. ❗🚫", show_alert=True)
            return
        
        if r.get('draw_started_manually', False) and len(r.get('current_draw_pool', [])) <= r['winners_count']:
            self.bot.answer_callback_query(call.id, "لقد وصلت إلى عدد الفائزين المطلوب بالفعل. ❗🚫", show_alert=True)
            return


        self.bot.answer_callback_query(call.id)

        if not r.get('draw_started_manually', False):
            r['draw_started_manually'] = True
            r['active'] = False
            r['current_draw_pool'] = set(r['participants'])
            self.bot.send_message(user_id, "بدأ السحب اليدوي! ✅🏁 اضغط 'استبعاد مشارك آخر' للمتابعة.")

        self._perform_draw(roulette_id)

    def handle_exclude_participant(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        parts = call.data.split("_")
        roulette_id = parts[2]
        participant_id = int(parts[3])
        user_id = call.from_user.id
        r = self.active_roulettes.get(roulette_id)

        if not r or user_id != r['creator_id']:
            self.bot.answer_callback_query(call.id, self.NOT_YOUR_COMMAND_MSG, show_alert=True)
            return

        self.bot.answer_callback_query(call.id)
        if participant_id in r['participants']:
            r['participants'].discard(participant_id)
            if r.get('draw_started_manually', False) or r['draw_method'] == 'automatic':
                r['current_draw_pool'].discard(participant_id)
            
            self.banned_from_creator_roulettes.setdefault(r['creator_id'], set()).add(participant_id)
            self._update_roulette_message(roulette_id)
            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"تم استبعاد المستخدم {participant_id} من هذا السحب وسحوباتك المستقبلية. ✅🗑️"
            )
        else:
            self.bot.send_message(user_id, "هذا المشارك ليس في السحب أو تم استبعاده مسبقاً. ❗❌")

    def handle_remind_me_roulette(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        roulette_id = call.data.split("_")[3]
        user_id = call.from_user.id
        r = self.active_roulettes.get(roulette_id)

        if not r:
            self.bot.answer_callback_query(call.id, "السحب غير موجود. ❗❌", show_alert=True)
            return

        self.bot.answer_callback_query(call.id)
        r['reminders'].add(user_id)
        self.bot.send_message(user_id, "سيتم إشعارك إذا فزت في هذا السحب! 🔔✅")

    def handle_remind_me_global_info(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        self.bot.answer_callback_query(call.id, "للتذكير، يجب عليك تفعيل زر التذكير لكل سحب على حدة في رسالة السحب. هذا الزر يعرض معلومات فقط. ℹ️", show_alert=True)

    def handle_view_participants(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        roulette_id = call.data.split("_")[2]
        user_id = call.from_user.id
        r = self.active_roulettes.get(roulette_id)

        if not r or user_id != r['creator_id']:
            self.bot.answer_callback_query(call.id, self.NOT_YOUR_COMMAND_MSG, show_alert=True)
            return
#This is released by a file by BBBBYB2 :: Syyad
        participants_to_show = r['current_draw_pool'] if r.get('draw_started_manually', False) or r['draw_method'] == 'automatic' else r['participants']
        participants_count = len(participants_to_show)
        self.bot.answer_callback_query(call.id, f"عدد المشاركين الحاليين: {participants_count} 👥ℹ️", show_alert=True)

        if not participants_to_show:
            self.bot.send_message(user_id, "لا يوجد مشاركون حالياً في هذا السحب. 🚫")
            return

        participants_list = []
        for p_id in participants_to_show:
            try:
                p_info = self.bot.get_chat(p_id)
                p_name = p_info.first_name if p_info.first_name else "مجهول"
                p_username = f" (@{p_info.username})" if p_info.username else ""
                participants_list.append(f"👤 {p_name}{p_username} (ID: {p_id})")
            except Exception:
                participants_list.append(f"👤 المستخدم (ID: {p_id})")

        message_text = "قائمة المشاركين الحاليين:\n" + "\n".join(participants_list)
        self.bot.send_message(user_id, message_text)

    def handle_show_help_info(self, call):
        if not self._check_bot_status_callback(call):
            return
        if not self._check_global_forced_subscription_callback(call):
            return
        self.bot.answer_callback_query(call.id)
        help_text = (
            "دليل استخدام بوت الروليت:\n\n"
            "1. **إضافة قناة (قنواتي):**\n"
            "   - اضغط على 'إضافة قناة ➕'.\n"
            "   - أضف البوت كمشرف في قناتك وأعطه الصلاحيات اللازمة (خاصة إرسال الرسائل).\n"
            "   - قم بإعادة توجيه أي رسالة من قناتك إلى البوت.\n"
            "   - سيتم ربط القناة بنجاح ويمكنك استخدامها لإنشاء السحوبات. 🔗 \n\n"
            "2. **بدء روليت:**\n"
            "   - اضغط على 'بدء روليت 🎲' واختر القناة التي أضفتها مسبقاً.\n"
            "   - **اختر نوع الروليت:**\n"
            "     - **الروليت العادي:** سحب بسيط بدون شروط إضافية.\n"
            "     - **الروليت المحمي:** يمنع المشاركين الذين قمت باستبعادهم مسبقاً من الانضمام مجدداً إلى سحوباتك.\n"
            "   - **اختر طريقة السحب:**\n"
            "     - **سحب يدوي:** أنت تتحكم بتوقيت كل استبعاد حتى الوصول لعدد الفائزين المطلوب.\n"
            "     - **سحب تلقائي:** يتم تحديد موعد نهائي، وعندها سيبدأ البوت تلقائياً باستبعاد المشاركين بشكل متتابع حتى الوصول لعدد الفائزين.\n"
            "   - **إرسال كليشة السحب 🎨:** هذه هي الرسالة التي ستظهر في القناة، يمكنك استخدام تنسيقات HTML (مثل التشويش `<code>&lt;tg-spoiler&gt;&lt;/tg-spoiler&gt;</code>`، التعريض `<code>&lt;b&gt;&lt;/b&gt;</code>`، أو المائل `<code>&lt;i&gt;&lt;/i&gt;</code>`).\n"
            "   - **إضافة قناة شرط (اختياري) 🔐:** يمكنك إضافة قناة إجبارية للانضمام لكي يتمكن المستخدم من المشاركة في السحب.\n"
            "   - **تحديد عدد الفائزين 🔢:** أدخل العدد النهائي للمشاركين الذين تريدهم أن يفوزوا. سيستمر السحب (يدوياً أو تلقائياً) باستبعاد المشاركين حتى يبقى هذا العدد.\n\n"
            "3. **إدارة الروليت بعد النشر:**\n"
            "   - ستظهر رسالة السحب في قناتك.\n"
            "   - **المشاركة في السحب 🎁:** للمستخدمين للانضمام.\n"
            "   - **ذكرني إذا فزت 🔔:** لتلقي إشعار خاص إذا فاز المستخدم.\n"
            "   - **التحكم بالاستبعاد (للمنشئ):**\n"
            "     - في السحب اليدوي، اضغط على 'ابدأ السحب 🏁' لبدء عملية الاستبعاد، ثم 'استبعاد مشارك آخر' للمتابعة.\n"
            "     - يمكنك تشغيل/إيقاف المشاركة قبل بدء السحب اليدوي.\n"
            "   - **عرض المشاركين 📊:** يعرض لك قائمة بالمشاركين الحاليين في السحب. 📈\n\n"
            "4. **استبعاد المشاركين (للمنشئ) 🚫:**\n"
            "   - عندما يشارك أحدهم في سحبك، ستتلقى رسالة خاصة في الدردشة مع البوت تتضمن زر 'استبعاد هذا المشارك ❌'. عند الضغط عليه، سيتم إزالة المستخدم من سحوباتك الحالية والمستقبلية إذا كان نوع الروليت 'محمي'."
        )
        self.bot.send_message(call.message.chat.id, help_text, parse_mode="HTML")

    def handle_admin_panel(self, call):
        user_id = call.from_user.id
        if user_id != self.ADMIN_ID:
            self.bot.answer_callback_query(call.id, self.NOT_YOUR_COMMAND_MSG, show_alert=True)
            return
        self.bot.answer_callback_query(call.id)
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="لوحة الأدمن ⚙️:",
            reply_markup=self.admin_panel_kb()
        )

    def handle_show_bot_stats(self, call):
        user_id = call.from_user.id
        if user_id != self.ADMIN_ID:
            self.bot.answer_callback_query(call.id, self.NOT_YOUR_COMMAND_MSG, show_alert=True)
            return
        self.bot.answer_callback_query(call.id)

        total_bound_channels = sum(len(channels) for channels in self.user_bound_channels.values())
        total_active_roulettes = len(self.active_roulettes)
        total_global_forced_channels = len(self.global_forced_channels)

        stats_text = (
            f"إحصائيات البوت: 📊\n"
            f"عدد المستخدمين الكلي: {self.total_users_count}\n"
            f"عدد القنوات المربوطة من المستخدمين: {total_bound_channels}\n"
            f"عدد الروليتات النشطة حالياً: {total_active_roulettes}\n"
            f"عدد قنوات الاشتراك الإجباري العالمية: {total_global_forced_channels}\n"
            f"حالة البوت: {'نشط' if self.bot_active else 'متوقف للصيانة'}"
        )
        self.bot.send_message(call.message.chat.id, stats_text)

    def handle_add_global_forced_channel_prompt(self, call):
        user_id = call.from_user.id
        if user_id != self.ADMIN_ID:
            self.bot.answer_callback_query(call.id, self.NOT_YOUR_COMMAND_MSG, show_alert=True)
            return
        self.bot.answer_callback_query(call.id)
        self.bot.send_message(call.message.chat.id, "أضف البوت كمشرف في القناة الإجبارية ثم أعد توجيه أي رسالة من القناة إلى هنا لإضافتها.")
        self.user_states[user_id] = 'awaiting_global_forced_channel_forward'

    def handle_remove_global_forced_channel_prompt(self, call):
        user_id = call.from_user.id
        if user_id != self.ADMIN_ID:
            self.bot.answer_callback_query(call.id, self.NOT_YOUR_COMMAND_MSG, show_alert=True)
            return
        self.bot.answer_callback_query(call.id)

        if not self.global_forced_channels:
            self.bot.send_message(call.message.chat.id, "لا توجد قنوات اشتراك إجباري لإزالتها. ❗❌")
            return

        remove_kb = InlineKeyboardMarkup()
        for cid, c_info in self.global_forced_channels.items():
            remove_kb.add(InlineKeyboardButton(f"{c_info.get('title', 'غير معروف')} 🗑️", callback_data=f"remove_global_channel__{cid}"))
        remove_kb.add(InlineKeyboardButton("رجوع 🔙", callback_data="admin_panel"))
        
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="اختر قناة الاشتراك الإجباري لإزالتها:",
            reply_markup=remove_kb
        )
        self.user_states[user_id] = 'awaiting_global_forced_channel_removal_selection'
#This is released by a file by BBBBYB2 :: Syyad
    def handle_remove_global_channel_selection(self, call):
        user_id = call.from_user.id
        if user_id != self.ADMIN_ID:
            self.bot.answer_callback_query(call.id, self.NOT_YOUR_COMMAND_MSG, show_alert=True)
            return
        self.bot.answer_callback_query(call.id)
        channel_id_str = call.data.split("__")[1]
        channel_id = int(channel_id_str)

        if channel_id in self.global_forced_channels:
            channel_info = self.global_forced_channels.pop(channel_id)
            self.bot.send_message(call.message.chat.id, f"تم إزالة قناة الاشتراك الإجباري: {channel_info.get('title', 'غير معروف')}. ✅🗑️")
        else:
            self.bot.send_message(call.message.chat.id, "هذه القناة ليست من قنوات الاشتراك الإجباري. ❗❌")
        self.handle_admin_panel(call)

    def handle_stop_bot_for_maintenance(self, call):
        user_id = call.from_user.id
        if user_id != self.ADMIN_ID:
            self.bot.answer_callback_query(call.id, self.NOT_YOUR_COMMAND_MSG, show_alert=True)
            return
        self.bot.answer_callback_query(call.id)
        self.bot_active = False
        self.bot.send_message(call.message.chat.id, "تم إيقاف البوت للصيانة. لن يتمكن المستخدمون العاديون من التفاعل معه الآن. 🔴")
        self.handle_admin_panel(call)

    def handle_start_bot_from_maintenance(self, call):
        user_id = call.from_user.id
        if user_id != self.ADMIN_ID:
            self.bot.answer_callback_query(call.id, self.NOT_YOUR_COMMAND_MSG, show_alert=True)
            return
        self.bot.answer_callback_query(call.id)
        self.bot_active = True
        self.bot.send_message(call.message.chat.id, "تم تشغيل البوت. يمكن للمستخدمين التفاعل معه الآن. 🟢")
        self.handle_admin_panel(call)

    def handle_messages_by_state(self, message: Message):
        user_id = message.from_user.id
        if not self._check_bot_status(message):
            return
        #This is released by a file by BBBBYB2 :: Syyad
        if not self._check_global_forced_subscription_message(message):
            return

        current_state = self.user_states.get(user_id)

        if current_state == 'awaiting_channel_to_add_forward':
            if message.forward_from_chat and message.forward_from_chat.type == "channel":
                channel = message.forward_from_chat
                try:
                    bot_member = self.bot.get_chat_member(channel.id, self.bot.get_me().id)
                    if bot_member.status not in ['administrator', 'creator']:
                        self.bot.send_message(message.chat.id, "البوت ليس مشرفاً في هذه القناة. الرجاء إضافة البوت كمشرف وإعادة التوجيه. ❗❌")
                        return
                except Exception:
                    self.bot.send_message(message.chat.id, "حدث خطأ أثناء التحقق من صلاحيات البوت في القناة. تأكد من أن القناة عامة وأن البوت مشرف. ❗⚠️")
                    return

                self.user_bound_channels.setdefault(user_id, {})[channel.id] = {
                    'title': channel.title,
                    'username': channel.username
                }
                self.bot.send_message(message.chat.id, f"تم ربط القناة: {channel.title} (@{channel.username if channel.username else 'غير متوفر'}) ✅🔗")
                self.user_states.pop(user_id, None)
                self.handle_my_channels_menu(message)
            else:
                self.bot.send_message(message.chat.id, "يرجى إعادة توجيه رسالة من قناة عامة أضفت فيها البوت كمشرف. ❗↩️")

        elif current_state == 'awaiting_global_forced_channel_forward':
            if user_id != self.ADMIN_ID:
                self.bot.send_message(message.chat.id, self.NOT_YOUR_COMMAND_MSG)
                return
#This is released by a file by BBBBYB2 :: Syyad
            if message.forward_from_chat and message.forward_from_chat.type == "channel":
                channel = message.forward_from_chat
                try:
                    bot_member = self.bot.get_chat_member(channel.id, self.bot.get_me().id)
                    if bot_member.status not in ['administrator', 'creator']:
                        self.bot.send_message(message.chat.id, "البوت ليس مشرفاً في هذه القناة. الرجاء إضافة البوت كمشرف وإعادة التوجيه. ❗❌")
                        return
                except Exception:
                    self.bot.send_message(message.chat.id, "حدث خطأ أثناء التحقق من صلاحيات البوت في القناة. تأكد من أن القناة عامة وأن البوت مشرف. ❗⚠️")
                    return
                
                if channel.id in self.global_forced_channels:
                    self.bot.send_message(message.chat.id, "هذه القناة مضافة بالفعل كقناة اشتراك إجباري. ❗⚠️")
                else:
                    self.global_forced_channels[channel.id] = {
                        'title': channel.title,
                        'username': channel.username
                    }
                    self.bot.send_message(message.chat.id, f"تم إضافة القناة {channel.title} (@{channel.username if channel.username else 'غير متوفر'}) كقناة اشتراك إجباري عالمي. ✅")
                self.user_states.pop(user_id, None)
                self.handle_admin_panel(message)
            else:
                self.bot.send_message(message.chat.id, "يرجى إعادة توجيه رسالة من قناة عامة أضفت فيها البوت كمشرف. ❗↩️")

        elif current_state == 'awaiting_roulette_text' or current_state == 'awaiting_roulette_text_edit':
            self.user_temp_data[user_id]['roulette_text'] = message.text

            if current_state == 'awaiting_roulette_text':
                self.bot.send_message(message.chat.id, "تم حفظ الكليشة، اختر أحد الخيارات: ✅💾", reply_markup=self.roulette_creation_options_kb())
            else:
                self.bot.send_message(message.chat.id, "تم تحديث الكليشة، اختر أحد الخيارات: ✅🔄", reply_markup=self.roulette_creation_options_kb())

            self.user_states[user_id] = 'awaiting_roulette_options_choice'

        elif current_state == 'awaiting_conditional_channel_link':
            channel_link = message.text.strip()
            channel_identifier = self._get_channel_info_from_link(channel_link)

            if not channel_identifier:
                self.bot.send_message(message.chat.id, "الرابط غير صالح. الرجاء إرسال رابط قناة صحيح (مثال: @YourChannel أو https://t.me/YourChannel). ❗❌")
                return

            try:
                chat = self.bot.get_chat(channel_identifier)
                if chat.type != 'channel':
                    self.bot.send_message(message.chat.id, "هذا ليس رابط قناة. الرجاء إرسال رابط قناة. ❗❌")
                    return
#This is released by a file by BBBBYB2 :: Syyad
                self.user_temp_data[user_id]['conditional_channel_id'] = chat.id
                self.user_temp_data[user_id]['conditional_channel_username'] = chat.username
                self.bot.send_message(message.chat.id, f"تم حفظ القناة الشرطية: {chat.title} (@{chat.username or 'غير متوفر'}) ✅")
                self.bot.send_message(message.chat.id, "كم عدد الفائزين الذين تريد اختيارهم؟ 📝🔢\n(سيتوقف السحب حين يصل عدد المشاركين المتبقين لهذا العدد).")
                self.user_states[user_id] = 'awaiting_winner_count'

            except telebot.apihelper.ApiTelegramException as e:
                if "chat not found" in str(e).lower() or "bad request" in str(e).lower():
                    self.bot.send_message(message.chat.id, "لم أتمكن من العثور على هذه القناة. تأكد من صحة الرابط. ❗🔍")
                else:
                    self.bot.send_message(message.chat.id, f"حدث خطأ: {e} ❗⚠️")
            except Exception:
                self.bot.send_message(message.chat.id, "حدث خطأ غير متوقع أثناء التحقق من القناة. ❗⚠️")

        elif current_state == 'awaiting_winner_count':
            try:
                count = int(message.text)
                if count < 0:
                    raise ValueError("Non-negative number required")
                self.user_temp_data[user_id]['winners_count'] = count
                self._publish_roulette(user_id)
                self.user_states.pop(user_id, None)
                self.user_temp_data.pop(user_id, None)
            except ValueError:
                self.bot.send_message(message.chat.id, "الرجاء إرسال عدد صحيح موجب أو صفر (في حال أردت استبعاد الجميع عدا واحد فقط مثلاً). ❗❌")
            except Exception as e:
                self.bot.send_message(message.chat.id, f"حدث خطأ أثناء نشر الروليت: {e} ❗⚠️")
                self.user_states.pop(user_id, None)
                self.user_temp_data.pop(user_id, None)
#This is released by a file by BBBBYB2 :: Syyad
        elif current_state == 'awaiting_auto_draw_value':
            try:
                value = int(message.text)
                if value <= 0:
                    raise ValueError("Positive number required")

                unit = self.user_temp_data[user_id].get('auto_draw_unit')
                delay_seconds = 0

                if unit == 'minutes':
                    delay_seconds = value * 60
                elif unit == 'hours':
                    delay_seconds = value * 3600
                elif unit == 'days':
                    delay_seconds = value * 86400
                else:
                    raise ValueError("Invalid unit")

                self.user_temp_data[user_id]['draw_time_unix'] = int(time.time() + delay_seconds)

                self.bot.send_message(message.chat.id, self.ROULETTE_TEXT_PROMPT, parse_mode="HTML")
                self.user_states[user_id] = 'awaiting_roulette_text'
#This is released by a file by BBBBYB2 :: Syyad
            except ValueError:
                self.bot.send_message(message.chat.id, "الرجاء إرسال عدد صحيح موجب للمدة الزمنية. ❗❌")
            except Exception as e:
                self.bot.send_message(message.chat.id, f"حدث خطأ: {e} ❗⚠️")
                self.user_states.pop(user_id, None)
                self.user_temp_data.pop(user_id, None)

        elif not message.text.startswith('/'):
            self.bot.send_message(message.chat.id, "أمر غير مفهوم. الرجاء استخدام الأزرار أو /start للبدء. ❗❓", reply_markup=self.main_menu_kb(user_id))
#This is released by a file by BBBBYB2 :: Syyad
    def run(self):
        self.bot.infinity_polling()

if __name__ == '__main__':
    bot_instance = RouletteBot()
    bot_instance.run()
#This is released by a file by BBBBYB2 :: Syyad