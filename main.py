import os
import json
import telegram
import asyncio

# Get secrets from environment variables and strip whitespace
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
chat_ids_str = os.environ.get("TELEGRAM_CHAT_IDS", "").strip()
CHAT_IDS = [chat_id.strip() for chat_id in chat_ids_str.split(',') if chat_id.strip()]

# Path to the questions file
QUESTIONS_FILE = 'questions.json'
# Path to the file that stores the index of the last question sent
LAST_INDEX_FILE = 'last_question_index.txt'

def get_last_index():
    """Reads the index of the last question sent from the file."""
    if os.path.exists(LAST_INDEX_FILE):
        with open(LAST_INDEX_FILE, 'r') as f:
            content = f.read().strip()
            if content:
                return int(content)
    return 0

def update_last_index(index):
    """Updates the index of the last question sent."""
    with open(LAST_INDEX_FILE, 'w') as f:
        f.write(str(index))

async def main():
    """Main function to send the questions."""
    if not BOT_TOKEN or not CHAT_IDS:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_IDS environment variables are not set or are empty.")
        return

    bot = telegram.Bot(token=BOT_TOKEN)

    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            questions = json.load(f)
    except FileNotFoundError:
        print(f"Error: {QUESTIONS_FILE} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {QUESTIONS_FILE}.")
        return

    last_index = get_last_index()

    if last_index >= len(questions):
        message = "All questions have been sent. We are done!"
        print(message)
        for chat_id in CHAT_IDS:
            try:
                await bot.send_message(chat_id=chat_id, text=message)
            except Exception as e:
                print(f"Failed to send completion message to {chat_id}: {e}")
        return

    questions_to_send = questions[last_index : last_index + 20]

    for question_data in questions_to_send:
        try:
            question = question_data['question']
            options = [opt.split(') ', 1)[1] if ') ' in opt else opt for opt in question_data['options']]
            correct_option_letter = question_data['answer'].split(')')[0]
            correct_option_index = ord(correct_option_letter.upper()) - ord('A')

            for chat_id in CHAT_IDS:
                try:
                    await bot.send_poll(
                        chat_id=chat_id,
                        question=f"Q{question_data['id']}: {question}",
                        options=options,
                        type=telegram.Poll.QUIZ,
                        correct_option_id=correct_option_index,
                        is_anonymous=False
                    )
                except Exception as e:
                    print(f"Failed to send question {question_data.get('id', 'N/A')} to {chat_id}: {e}")
            await asyncio.sleep(1)  # Small delay to avoid hitting rate limits
        except (KeyError, IndexError) as e:
            print(f"Skipping malformed question data: {question_data}. Error: {e}")
            continue

    new_index = last_index + len(questions_to_send)
    update_last_index(new_index)
    print(f"Successfully sent {len(questions_to_send)} questions. Next batch will start from index {new_index}.")

if __name__ == "__main__":
    asyncio.run(main())