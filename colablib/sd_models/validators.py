import os
import gc
import torch
import json
import hashlib
import json
from typing import Optional
from pydantic import BaseModel, ValidationError
from safetensors.torch import load_file, safe_open
from ..colored_print import cprint

class LoraArgs(BaseModel):
    conv_dim: Optional[int]
    conv_alpha: Optional[float]
    algo: Optional[str]
    unit: Optional[str]

class Metadata(BaseModel):
    ss_network_args: Optional[str]
    ss_network_dim: Optional[int]
    ss_network_alpha: Optional[float]
    ss_network_module: Optional[str]
    lora_key_encoding: Optional[str]

    class Config:
        arbitrary_types_allowed = True

class Validator:
    """
    Validator is a helper class for validating models, vae, and lora. 
    It provides utility methods for checking and loading different types of files.
    """

    @staticmethod
    def is_safetensors(path):
        """
        Checks if the given path corresponds to a safetensors file.
        """
        return os.path.splitext(path)[1].lower() == '.safetensors'

    @staticmethod
    def is_ckpt(path):
        """
        Checks if the given path corresponds to a checkpoint file.
        """
        return os.path.splitext(path)[1].lower() == '.ckpt'

    @staticmethod
    def validate_model(model_path, map_location="cpu"):
        """
        Validates the model by attempting to load it.
        """
        if Validator.is_safetensors(model_path):
            try:
                tmp = load_file(model_path, device=map_location)
                del tmp
                gc.collect()
                torch.cuda.empty_cache()
            except Exception as e:
                print(e)
                new_model_path = os.path.splitext(model_path)[0] + ".ckpt"
                os.rename(model_path, new_model_path)
                cprint(f"Model Info: model renamed to {os.path.basename(new_model_path)}", color="green")
                return new_model_path
        elif Validator.is_ckpt(model_path):
            try:
                tmp = torch.load(model_path, map_location=map_location)
                del tmp
                gc.collect()
                torch.cuda.empty_cache()
            except Exception as e:
                cprint(e)
                new_model_path = os.path.splitext(model_path)[0] + ".safetensors"
                os.rename(model_path, new_model_path)
                cprint(e, f"Model Info: model renamed to {os.path.basename(new_model_path)}", color="green")
                return new_model_path
        return None
    
    @staticmethod
    def validate_vae(vae_path):
        """
        Validates the vae by checking if its sha256 hash is in the expected hash list.
        """
        expected_hash = {
            'Animevae'                                : 'f921fb3f29891d2a77a6571e56b8b5052420d2884129517a333c60b1b4816cdf',
            'kl-f8-anime'                             : '2f11c4a99ddc28d0ad8bce0acc38bed310b45d38a3fe4bb367dc30f3ef1a4868',
            'kl-f8-anime2'                            : 'df3c506e51b7ee1d7b5a6a2bb7142d47d488743c96aa778afb0f53a2cdc2d38d',
            'autoencoder_fix_kl-f8-trinart_characters': '2453b80bc1716bc3f94496d4e56be891e267051dc43c5144f384b66a73ac8295',
            'vae-ft-mse-840000-ema-pruned'            : 'c6a580b13a5bc05a5e16e4dbb80608ff2ec251a162311590c1f34c013d7f3dab',
            'mse840000_klf8anime'                     : '53cfd845736459e78f208786f8d56109093f37dc427e366769416f6ca9ea6fc9',
            'mse840000_klf8anime_klf8anime2'          : 'a9a44822203eaa05104d37a242ec5af405d0fcfb98a81fb89f0c2e8bb71ae962',
            'ClearVAE'                                : '600345c503784cd77536d714f0e4c43f9e1fa4379007e730d54c454c66ee36db',
            'ClearVAE-NansLessTest'                   : '4809659b70d67d314c45062ece33a7f9f8abc9aaf13805173a129cad2664e091',
            'ClearVAE-Variant'                        : '9c2d6dc265bd4758042cc2385b090aede02d8160b556830e9385db8a74ddcaab', 
            'ACertainThing-0064'                      : '319adc806290ec775f361bac6c68a878a96c9982e1dd77c9545240cc811c4e58',
            'flat_paint_b_v2'                         : '2da3f767874561a7e0e52ef2c24c8a0ea2997fd267727cfd2981fd9594e8bbd4',
            'flat_paint_b_v3'                         : '0b4ff3b7be8c164b2a80d3a3a7c5eebc41a11994420a8633abf8190cff9cfc9c',
            'SD15NewVAEpruned'                        : '27a4ac756c5c4fb25bfb7bd32a700a89fe77a66926338b1d78b97e25e1e85f75'
        }
        with open(vae_path, 'rb') as file:
            contents = file.read()
        sha256_hash = hashlib.sha256(contents).hexdigest()
        for vae_name, hash_value in expected_hash.items():
            if hash_value == sha256_hash:
                cprint(f"VAE Info: VAE shared the same sha256 with {vae_name}.", color="green")
                return

    @staticmethod
    def validate_lora(lora_path):
        """
        Validates lora by checking its metadata.
        """
        try:
            if Validator.is_safetensors(lora_path):
                with safe_open(lora_path, framework="pt") as f:
                    raw_metadata = f.metadata()

                if raw_metadata:
                    try:
                        metadata = Metadata(**raw_metadata)
                    except ValidationError as e:
                        cprint(f"Metadata validation error: {e}", color="flat_red")
                        return False, "Invalid metadata"

                    lora_args_dict = json.loads(metadata.ss_network_args) if metadata.ss_network_args else {}
                    
                    try:
                        lora_args = LoraArgs(**lora_args_dict)
                    except ValidationError as e:
                        cprint(f"Lora args validation error: {e}", color="flat_red")
                        return False, "Invalid lora args"

                    lora_type = Validator.validate_kohya_lora(
                        metadata.ss_network_module, lora_args.algo, lora_args.conv_dim, lora_args.conv_alpha
                    )

                    if lora_type:
                        data_dict = {
                            "type"      : lora_type,
                            "dim"       : metadata.ss_network_dim,
                            "alpha"     : metadata.ss_network_alpha,
                            "conv_dim"  : lora_args.conv_dim,
                            "conv_alpha": lora_args.conv_alpha,
                            "algo"      : lora_args.algo,
                            "unit"      : lora_args.unit,
                        }

                        json_output_path = os.path.splitext(lora_path)[0] + '.json'

                        with open(json_output_path, 'w') as outfile:
                            json.dump(data_dict, outfile, indent=4)

                        output_list = [f"{key}: {value}" for key, value in data_dict.items() if value is not None]

                        return True, f"LoRA Info: {output_list}"
                    elif metadata.lora_key_encoding is not None:
                        return False, "LoRA Info: LoRA is not trained using 'kohya-ss/sd-scripts' but using 'd8ahazard/sd_dreambooth_extension'"
                else:
                    return True, "LoRA Info: No metadata saved"
            else:
                return True, "LoRA Info: No metadata saved, your model is not in safetensors format"
        except Exception as e:
            cprint(f"An error occurred: {str(e)}", color="flat_red")

    @staticmethod
    def validate_kohya_lora(lora_module, lora_algo, lora_conv_dim, lora_conv_alpha):
        """
        Validates kohya lora by checking its parameters.
        """
        lora_type = None

        if 'lycoris.kohya' in lora_module:
            if lora_algo:
                if "locon" in lora_algo or "lora" in lora_algo:
                    lora_type = "LoCon"
                elif "loha" in lora_algo:
                    lora_type = "LoHA"
                elif "lokr" in lora_algo:
                    lora_type = "LoKR"
                elif "ia3" in lora_algo:
                    lora_type = "IA3"
                elif "dylora" in lora_algo:
                    lora_type = "DyLoRA_LyCORIS"
        elif 'networks.lora' in lora_module:
            if lora_conv_dim is not None or lora_conv_alpha is not None:
                lora_type = "LoRA_C3Lier"
            else:
                lora_type = "LoRA_LierLa"
        elif 'networks.dylora' in lora_module:
            if lora_conv_dim is not None or lora_conv_alpha is not None:
                lora_type = "DyLoRA_C3Lier"
            else:
                lora_type = "DyLoRA_LierLa"
        else:
            lora_type = None

        return lora_type