"""
Creates algorithm configuration for PPO and starts training process
"""

import os

import ray
from ray.rllib.algorithms.ppo import PPOConfig
from train import train
from dcrl_eplus_env import DCRLeplus
from dcrl_env import DCRL
from utils.rllib_callbacks import CustomCallbacks

# Data collection config
TIMESTEP_PER_HOUR = 4
COLLECTED_DAYS = 7
NUM_AGENTS = 3
NUM_WORKERS = 31
NUM_GPU = 0

CONFIG = (
        PPOConfig()
        .environment(
            env=DCRL if not os.getenv('EPLUS') else DCRLeplus,
            env_config={
                # Agents active
                'agents': ['agent_ls', 'agent_dc', 'agent_bat'],

                # Datafiles
                'location': 'ny',
                'cintensity_file': 'NYIS_NG_&_avgCI.csv',
                'weather_file': 'USA_NY_New.York-Kennedy.epw',
                'workload_file': 'Alibaba_CPU_Data_Hourly_1.csv',

                # Battery capacity
                'max_bat_cap_Mw': 2,
                
                # Collaborative weight in the reward
                'individual_reward_weight': 0.8,
                
                # Flexible load ratio
                'flexible_load': 0.1,
                
                # Specify reward methods
                'ls_reward': 'default_ls_reward',
                'dc_reward': 'default_dc_reward',
                'bat_reward': 'default_bat_reward'
            }
        )
        .framework("torch")
        .rollouts(num_rollout_workers=NUM_WORKERS)
        .training(
            gamma=0.99, 
            lr=1e-5, 
            lr_schedule=[[0, 3e-5], [10000000, 1e-6]],
            kl_coeff=0.3, 
            clip_param=0.02,
            entropy_coeff=0.05,
            use_gae=True, 
            train_batch_size=24 * TIMESTEP_PER_HOUR * COLLECTED_DAYS * NUM_WORKERS * NUM_AGENTS,
            model={'fcnet_hiddens': [128, 64, 16], 'fcnet_activation': 'relu'}, 
            shuffle_sequences=True
        )
        .callbacks(CustomCallbacks)
        .resources(num_cpus_per_worker=1, num_gpus=NUM_GPU)
    )

NAME = "test"
RESULTS_DIR = './results'

if __name__ == '__main__':
    os.environ["RAY_DEDUP_LOGS"] = "0"

    ray.init(ignore_reinit_error=True)
    #ray.init(local_mode=True, ignore_reinit_error=True)

    train(
        algorithm="PPO",
        config=CONFIG,
        results_dir=RESULTS_DIR,
        name=NAME,
    )