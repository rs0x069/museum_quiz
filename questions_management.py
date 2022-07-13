import os
import random
import re


def load_questions():
    files_folder = 'quiz-questions'

    try:
        quiz_files = [
            os.path.join(files_folder, filename)
            for filename in os.listdir(files_folder)
            if os.path.isfile(os.path.join(files_folder, filename))
        ]
        quiz_files.sort()
    except OSError as err:
        print(f'OSError: {err}')
        return False

    quiz_questions = []
    try:
        for quiz_file in quiz_files[:1]:
            with open(quiz_file, 'r', encoding='KOI8-R') as readable_file:
                for line in readable_file:
                    if re.search(r'^Вопрос\s\d+:$', line):
                        search_pattern = ''
                        question = ''
                        while search_pattern != '\n':
                            search_pattern = readable_file.readline()
                            question += search_pattern.replace('\n', ' ')
                        question = question.rstrip()

                        # Method 1 to find answer
                        # while readable_file.readline() != 'Ответ:\n':
                        #     next(readable_file)
                        # answer = readable_file.readline().rstrip()

                    # Method 2 to find answer
                    if re.search(r'^Ответ:$', line):
                        answer = readable_file.readline().rstrip()
                        answer_lowercase = answer.translate({ord(c): None for c in '."[]'}).strip().lower()

                        quiz_questions.append({
                            'Вопрос': question,
                            'Ответ': answer_lowercase
                        })
    except OSError as err:
        print(f'OSError: {err}')
    else:
        return quiz_questions


def get_random_quiz_question():
    quiz_questions = load_questions()
    random_number_questions = random.randint(0, len(quiz_questions) - 1)
    return quiz_questions[random_number_questions]['Вопрос']


def get_correct_answer(wished_question):
    for quiz_question in load_questions():
        if quiz_question['Вопрос'] == wished_question:
            return quiz_question['Ответ']
    return None
