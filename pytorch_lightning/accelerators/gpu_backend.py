# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from pytorch_lightning.accelerators.base import LightningBackend
from pytorch_lightning.core import LightningModule
from pytorch_lightning.utilities import AMPType

try:
    from apex import amp
except ImportError:
    amp = None


class GPUBackend(LightningBackend):
    amp_type: AMPType

    def setup(self, model):
        super().setup(model)

        model.cuda(self._trainer.root_gpu)

        # CHOOSE OPTIMIZER
        # allow for lr schedulers as well
        optimizers, lr_schedulers, optimizer_frequencies = self._trainer.init_optimizers(model)
        self._trainer.optimizers = optimizers
        self._trainer.lr_schedulers = lr_schedulers
        self._trainer.optimizer_frequencies = optimizer_frequencies

        if self._trainer.amp_type == AMPType.APEX:
            model = self._setup_nvidia_apex(model)
        return model

    def train(self):
        results = self._trainer.run_pretrain_routine(self._model)
        return results

    def _setup_nvidia_apex(self, model: LightningModule):
        model, optimizers = model.configure_apex(amp, model, self._trainer.optimizers, self._trainer.amp_level)
        self._trainer.optimizers = optimizers
        self._trainer.reinit_scheduler_properties(self._trainer.optimizers, self._trainer.lr_schedulers)
        return model
