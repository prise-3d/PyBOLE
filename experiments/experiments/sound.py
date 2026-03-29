from ..models import SessionProgress
import os
import random
from django.conf import settings
from abc import abstractmethod


class SoundSessionProgress(SessionProgress):
    @abstractmethod
    def start(self, participant_data):

        # need to be initialized in order to start experiment
        if self.data is None:
            self.data = {}

        self.data['iteration'] = 0
        self.data['participant'] = {
            'know-cg': participant_data['basic-info-know-cg'],
            'why': participant_data['basic-info-why'],
            'glasses': participant_data['basic-info-glasses'],
        }

        # always save state
        self.save()

    @abstractmethod
    def next(self, step, answer) -> dict:
        # 1. update previous step depending of answer (if previous step exists)
        if step is not None and 'binary-answer-time' in answer:

            answer_time = answer['binary-answer-time']
            answer_value = answer['binary-answer-value']

            step.data['answer_time'] = answer_time
            step.data['answer_value'] = answer_value
            step.save()

        # 2. process next step data (can be depending of answer)

        # folder of images could also stored into experiment config
        sound_path = 'resources/sounds/animals'

        # need to take care of static media folder (static folder need to be removed)
        sounds_path = sorted([
                    os.path.join(sound_path, sound)
                    for sound in os.listdir(os.path.join(settings.RELATIVE_STATIC_URL, sound_path))
                ])

        # prepare next step data with random image path
        step_data = {
            "sound": {
                "src": f"{random.choice(sounds_path)}"
            }
        }

        # 3. increment iteration into progress data
        self.data['iteration'] += 1


        
        # always save state
        self.save()

        # return new step data
        return step_data
        
    @abstractmethod
    def progress(self) -> float:

        # access of session's config from current SessionProgress instance
        total_iterations = int(self.session.config['max_iterations'])
        iteration = int(self.data['iteration'])

        # return percent of session advancement
        return (iteration / total_iterations) * 100

    @abstractmethod
    def end(self) -> bool:

        total_iterations = int(self.session.config['max_iterations'])
        iteration = int(self.data['iteration'])

        return iteration > total_iterations
        
