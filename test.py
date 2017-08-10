from limix_lsf import BJob

fp = '/hps/nobackup/stegle/users/horta/Scratch/h2/bernoulli/all.10p/nan:nan:0.5:0.0:8000:Bernoulli-FastGLMM:1000:100:nan:0.01:0:50000'

fp_out = fp + '.out'
fp_err = fp + '.err'

bjob = BJob(fp_out=fp_out, fp_err=fp_err)
print(bjob.submitted)
