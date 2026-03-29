import os, sys
import random
import numpy as np
from PIL import Image
from ..models import SessionProgress, SessionStep
from django.conf import settings
import pickle

# include specific requirements for Quest
from .classes.quest_plus import QuestPlus
from .classes.quest_plus import psychometric_fun

def get_nsamples_image(filename):
    """Specific method in order to get number of samples of image
    Args:
        filename ([str]): filename on expected image 
    Returns:
        [int]: number of samples
    """
    return int(filename.split('_')[-1].replace('.png', ''))

class QuestSessionProgress(SessionProgress):
    """
    Example of Quest experiment with specific number of iteration
    """    
    
    def start(self, participant_data):
        """
        Define and init some progress variables
        """

        # need to be initialized in order to start experiment
        if self.data is None:
            self.data = {}

        self.data['iteration'] = 0
        self.data['participant'] = {
            'know-cg': participant_data['basic-info-know-cg'],
            'why': participant_data['basic-info-why'],
            'glasses': participant_data['basic-info-glasses'],
        }

        slopes = np.arange(0.0001, 0.001, 0.00003, 'float32')
        stim = np.arange(500, 10500, 500, 'int32')

        # need basic types
        self.data['slopes'] = list([ float(s) for s in slopes ])
        self.data['stim'] = list([ float(s) for s in stim ]) # 10500 because we need 10000 too

        # initialization of Quest plus instance (require numpy array)
        qp = QuestPlus(stim, [stim, slopes], 
                        function=psychometric_fun)

        # store participant quest binary data
        qp_bytes = pickle.dumps(qp)
        self.binary = qp_bytes

        # always save state
        self.save()

    def next(self, step, answer) -> dict:
        """
        Define next step data object taking into account current step and answer

        Return: JSON data object
        """
        # load Quest plus instance
        qp = pickle.loads(self.binary)

        # Initialize and get experiment configuration parameters
        entropy = sys.float_info.max
        previous_entropy = None

        # 1. update previous step depending of answer (if previous step exists)
        if step is not None and 'binary-answer-time' in answer:
            answer_time = int(answer['binary-answer-time'])
            answer_value = int(answer['binary-answer-value'])
            
            step.data['answer_time'] = answer_time
            step.data['answer_value'] = answer_value
            step.save()

            # update quest plus
            previous_entropy = step.data['entropy']
            previous_stim = step.data['stim']

            qp.update(int(previous_stim), answer_value) 

            threshold = qp.get_fit_params(select='mode')[0]
        
            # get new entropy
            entropy = qp.get_entropy()
            print(f'Quest+ model updated: current entropy {entropy}')
        
        # 2. process next step data (can be depending of answer)

        # folder of images could also stored into experiment config
        cornel_box_path = 'resources/images/cornel_box'

        # need to take care of static media folder
        images_path = sorted([ 
                    os.path.join(cornel_box_path, img) 
                    for img in os.listdir(os.path.join(settings.RELATIVE_STATIC_URL, cornel_box_path)) 
                ])

        # right image always display reference
        # prepare next step data
        # process `quest`
        if self.data['iteration'] <= 4: # at least 4 iterations

            next_stim_id = int(self.data['iteration'] * len(self.data['stim'])/10)
            next_stim = self.data['stim'][next_stim_id]
        else:
            next_stim = qp.next_contrast()

        # get the selected image path
        selected_image_path = [ img for img in os.listdir(os.path.join(settings.RELATIVE_STATIC_URL, cornel_box_path)) \
            if get_nsamples_image(img) == next_stim ][0]

        # reconstruct image
        # STATIC_URL should never be included in image path for template
        current_image = np.array(Image.open(os.path.join(settings.RELATIVE_STATIC_URL, cornel_box_path, selected_image_path)))
        ref_image = np.array(Image.open(os.path.join(settings.RELATIVE_STATIC_URL, images_path[-1])))

        h, w, _ = current_image.shape

        # here static merge
        current_image[int(h/2):h, int(w/2):w, :] = ref_image[int(h/2):h, int(w/2):w, :]

        # save generated image into static folder (need the access of the new image)
        generated_path = os.path.join(settings.RELATIVE_STATIC_URL, 'generated')

        if not os.path.exists(generated_path):
            os.makedirs(generated_path)

        output_image_path = os.path.join(generated_path, f'{self.participant.id}.png')
        Image.fromarray(current_image).save(output_image_path)

        if previous_entropy is not None:
            abs_entropy = abs(previous_entropy - entropy)
        else: 
            abs_entropy = sys.float_info.max

        # STATIC_URL should never be included into image path for template
        step_data = {
            "image": {
                "src": f"{output_image_path.replace(settings.RELATIVE_STATIC_URL, '')}",
                "width": 500,
                "height": 500
            },
            "stim": get_nsamples_image(selected_image_path),
            "entropy": entropy,
            'abs_entropy': abs_entropy # store the absolute difference entropy from last two steps
        }

        # increment iteration into progress data
        self.data['iteration'] += 1

        # store updated participant quest binary data
        qp_bytes = pickle.dumps(qp)
        self.binary = qp_bytes

        # always save state
        self.save()

        return step_data

    def progress(self) -> float:
        """
        Define the percent progress of the experiment

        Return: float progress between [0, 100]
        """
        total_iterations = int(self.session.config['max_iterations'])
        iteration = int(self.data['iteration'])

        # return percent of session advancement
        return (iteration / total_iterations) * 100

    def end(self) -> bool:
        """
        Check whether it's the end or not of the experiment

        Return: bool
        """
        max_iterations = int(self.session.config['max_iterations'])
        min_iterations = int(self.session.config['min_iterations'])
        iteration = int(self.data['iteration'])
        
        # retrieve from last step the absolute difference of entropy
        previous_step = SessionStep.objects.filter(progress_id=self.id).latest('created_on')
        abs_entropy = previous_step.data['abs_entropy']

        # stopping criterion based on entropy (could also be on max_time)
        return min_iterations <= iteration and (iteration >= max_iterations or abs_entropy < self.session.config['stop_entropy'])
   
