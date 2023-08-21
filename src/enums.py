from enum import Enum


class StrEnum(str, Enum):
    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


class EnvEnum(StrEnum):
    DEV: str = "dev"
    PROD: str = "prod"


class ResponseStatusEnum(StrEnum):
    PENDING: str = "pending"
    ASSIGNED: str = "assigned"
    COMPLETED: str = "completed"
    ERROR: str = "error"


class ErrorTitle(StrEnum):
    UNKNOWN: str = "Unknown Error"
    INPUT_VALIDATION: str = "Input Validation Error"
    TIMEOUT: str = "TimeOut Error"
    WRONG_TASK_ID: str = "Wrong Task ID Error"


class ModelEnum(StrEnum):
    STABLE_DIFFUSION_V2_1 = "stable-diffusion-v2-1"
    STABLE_DIFFUSION_V2_1_768 = "stable-diffusion-v2-1-768"


class ErrorMessage(StrEnum):
    UNKNOWN: str = "Unknown error occurred.\nPlease share the error with our community manager.\n"


class WarningMessages(StrEnum):
    NSFW: str = "Potential NSFW content was detected in one or more images.\nIf you want to see the original image, press the button below."


class SchedulerType(StrEnum):
    DDIM: str = "ddim"  # DDIMScheduler
    PNDM: str = "pndm"  # PNDMScheduler
    EULER_DISCRETE = "euler_discrete"  # EulerDiscreteScheduler
    EULER_ANCESTRAL_DISCRETE = "euler_ancestral_discrete"  # EulerAncestralDiscreteScheduler
    HEUN_DISCRETE = "heun_discrete"  # HeunDiscreteScheduler
    K_DPM_2_DISCRETE = "k_dpm_2_discrete"  # KDPM2DiscreteScheduler
    K_DPM_2_ANCESTRAL_DISCRETE = "k_dpm_2_ancestral_discrete"  # KDPM2AncestralDiscreteScheduler
    LMS_DISCRETE = "lms_discrete"  # LMSDiscreteScheduler
