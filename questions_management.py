import os
import random
import re


def load_questions():
    files_folder = 'quiz-questions'

    quiz_files = [
        os.path.join(files_folder, filename)
        for filename in os.listdir(files_folder)
        if os.path.isfile(os.path.join(files_folder, filename))
    ]
    quiz_files.sort()

    quiz_questions = []
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

                if re.search(r'^Ответ:$', line):
                    answer = readable_file.readline().rstrip()
                    answer_cleaned = answer.translate({ord(character): None for character in '."[]'}).strip()
                    answer_lowercase = answer_cleaned.lower()

                    quiz_questions.append({
                        'Вопрос': question,
                        'Ответ': answer_lowercase
                        })
    return quiz_questions


def get_random_quiz_question(quiz_questions):
    random_number_questions = random.randint(0, len(quiz_questions) - 1)
    return quiz_questions[random_number_questions]['Вопрос']


def get_correct_answer(quiz_questions, wished_question):
    for quiz_question in quiz_questions:
        if quiz_question['Вопрос'] == wished_question:
            return quiz_question['Ответ']
