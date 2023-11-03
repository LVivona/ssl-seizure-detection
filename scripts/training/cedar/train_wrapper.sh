#!/bin/bash

# Check if the patient ID is provided
if [ -z "$1" ]; then
    echo "Error: No patient ID provided."
    exit 1
fi

# The patient ID (e.g., jh101)
patient_id="$1"

# SSL Parameters
tau_pos="$2"
tau_neg="$3"

# Date and time ID
datetime_id="$4"

# Train, val, test split
split="$5"

# Model selection. It is 1-3 digits, where a 0 indicates supervised, 1 indicates relative positioning, and 2 indicates temporal shuffling.
# For example, model_selection=01 means that only the supervised and relative positioning models will be trained.
model_selection=${6:-}

# Training arguments
run_types=("combined" "all" "all")
model_ids=("supervised" "relative_positioning" "temporal_shuffling")
times=("00:45:00" "20:00:00" "20:00:00")

# Base directory
base_dir="${xav}/ssl_epilepsy/models/${patient_id}"
mkdir -p "${base_dir}" || { echo "Error: Cannot create directory ${base_dir}"; exit 1; }


# Function to keep elements by index
keep_by_indices() {
    local indices_to_keep=($1)
    local -n _arr=$2
    local -a new_arr=()
    for index in "${indices_to_keep[@]}"; do
        new_arr+=( "${_arr[index]}" )
    done
    _arr=("${new_arr[@]}") # Assign the filtered array back to the original array variable
}

if [ -n "$model_selection" ]; then
    # Convert model_selection string to an array of indices to keep
    indices_to_keep=()
    for (( i=0; i<${#model_selection}; i++ )); do
        indices_to_keep+=(${model_selection:$i:1})
    done

    # Keep only the models, run_types, and times that are in indices_to_keep
    keep_by_indices "${indices_to_keep[*]}" model_ids
    keep_by_indices "${indices_to_keep[*]}" run_types
    keep_by_indices "${indices_to_keep[*]}" times
    
else
    echo "Model selection is not set. Running all models..."
fi



# Iterate over each model and its corresponding time
for i in "${!model_ids[@]}"; do
    model_id="${model_ids[$i]}"
    time="${times[$i]}"
    job_name="training_${patient_id}_${model_id}_${time}"
    run_type="${run_types[$i]}"
    data_path="${xav}/ssl_epilepsy/data/patient_pyg/${patient_id}/${model_id}"
    
    if [ "$model_id" == "relative_positioning" ] || [ "$model_id" == "temporal_shuffling" ]; then
        data_path="${data_path}/${tau_pos}s_${tau_neg}s" 
    fi
    
    logdir="${base_dir}/${model_id}/${datetime_id}"
    mkdir -p "${logdir}"

    # Create a job for each model + time
    sbatch <<EOT
#!/bin/bash
#SBATCH --ntasks=1              # Number of tasks
#SBATCH --gres=gpu:v100l:1      # Number of Volta 100 GPUs
#SBATCH --cpus-per-task=8       # CPU cores/threads, AKA number of workers (num_workers)
#SBATCH --mem-per-cpu=12G       # memory per CPU core
#SBATCH --time="${time}"        # Time limit for the job  
#SBATCH --job-name="${job_name}"
#SBATCH --output="${xav}/ssl_epilepsy/jobs/training/${job_name}.out"
#SBATCH --error="${xav}/ssl_epilepsy/jobs/training/${job_name}.err"
#SBATCH --mail-user=xmootoo@gmail.com
#SBATCH --mail-type=ALL

cd "${xav}/ssl_epilepsy/ssl-seizure-detection/src"
module load cuda/11.7 cudnn python/3.10
source ~/torch2_cuda11.7/bin/activate

export WANDB_API_KEY="$WANDB_API_KEY"

python main.py "${data_path}" "${logdir}" "${patient_id}" "${model_id}" "${datetime_id}" "${run_type}" "${split}"
EOT
done
