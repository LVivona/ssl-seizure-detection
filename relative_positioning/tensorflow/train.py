import os
import pickle
import time


from tensorflow.keras.optimizers import Adam
from model import relative_positioning
from dataloader import dataloaders_torch
from evaluation import f1_score, training_curves, eval

start_time = time.time()


def run(data, fltrs_out, l2_reg, lr, epochs, batch_size, val_size, test_size, seed=0, es_patience=20, stats_logdir=None, 
        model_logdir=None, num_examples=50000):
    """
    Runnning the self-supervised model 'Relative Positioning' using a GNN encoder.

    Args:
        data (list): Graph pairs with pseudolabels of the form [[[A, NF, EF], [A', NF', EF']], Y].
        fltrs_out (int): Number of output filters for the GNN encoder.
        l2_reg (float): L2 regularization parameter.
        lr (float): Learning rate.
        epochs (int): Number of epochs.
        batch_size (int): Batch size (powers of 2).
        val_size (float): Size of validation set (from 0 to 1).
        test_size (_type_): Size of test set (from 0 to 1)
        seed (int, optional): Random seed. Defaults to 0.
        es_patience (int, optional): Patience parameter. Defaults to 20.
        stats_logdir (_type_, optional): Directory for saving model statistics. Defaults to None.
        model_logdir (_type_, optional): Directory for saving the model. Defaults to None.
    """
    
    
    # Get data loaders
    train_loader, val_loader, test_loader = dataloaders_torch(data, batch_size, val_size, test_size, seed, num_examples)
    
    # Model
    model = relative_positioning(fltrs_out, l2_reg)
    
    # Optimization algorithm
    optimizer = Adam(lr)
    
    # Compile model
    model.compile(optimizer=optimizer, loss="binary_crossentropy", metrics=["accuracy", "AUC", f1_score])
    
    # Metrics
    best_val_loss = 10000
    patience = es_patience
    train_loss = []
    train_acc = []
    train_auc = []
    train_f1_score = []
    val_loss = []
    val_acc = []
    val_auc = []
    val_f1_score = []
    saved_model = False
    
    for epoch in range(epochs):
        
        
        # ------------------------------ Training ------------------------------
        metrics = None
        
        # Adam optimization on batch
        t=0
        for batch in train_loader:
            inputs, labels = batch
            print(t)
            t+=1
            # e.g., input[0] = [[A, NF, EF], [A', NF', EF']]
            outs = model.train_on_batch(inputs, labels)
         
        # Training stats   
            for i, k in enumerate(model.metrics_names):
                if metrics is None:
                    metrics = {k: 0 for k in model.metrics_names}
                metrics[k] += outs[i] / len(train_loader)
        train_loss.append(metrics["loss"])
        train_acc.append(metrics["accuracy"])
        train_auc.append(metrics["auc"])
        train_f1_score.append(metrics["f1_score"])
        
        # Print loss
        print("Epoch: " + str(1 + epoch) + ". Loss: " + str(metrics["loss"]))
    
    
    # ------------------------------ Validation ------------------------------
        metrics_val = None
        for batch in val_loader:
            inputs, labels = batch
            
            # Convert to NumPy arrays
            inputs = [[inp.numpy() for inp in inputs[0]], [inp.numpy() for inp in inputs[1]]]         
            labels = labels.numpy()
            
            # Evaluate model
            outs = model.evaluate(inputs, labels)
            
            # Validation stats
            for i, k in enumerate(model.metrics_names):
                if metrics_val is None:
                    metrics_val = {k: 0 for k in model.metrics_names}
                metrics_val[k] += outs[i] / len(val_loader)
        val_loss.append(metrics_val["loss"])
        val_acc.append(metrics_val["accuracy"])
        val_auc.append(metrics_val["auc"])
        val_f1_score.append(metrics_val["f1_score"])
    
    
    # ------------------------------ Early stopping ------------------------------
    if metrics_val["loss"] < best_val_loss:
        best_val_loss = metrics_val["loss"]
        patience = es_patience
        model.save_weights(os.path.join(model_logdir, "best_model.h5"))
        saved_model = True
    else:
        patience -= 1
        if patience == 0:
            print("Early stopping (best val_loss: {})".format(best_val_loss))
    if not saved_model:
        model.save_weights(os.path.join(model_logdir, "best_model.h5"))
   
    
    # ------------------------------ Save best model ------------------------------
    model.load_weights(os.path.join(model_logdir, "best_model.h5"))


    # ------------------------------ Save statistical measurements ------------------------------
    train_val_stats = {
        'train_loss': train_loss,
        'train_acc': train_acc,
        'train_auc': train_auc,
        'train_f1_score': train_f1_score,
        'val_loss': val_loss,
        'val_acc': val_acc,
        'val_auc': val_auc,
        'val_f1_score': val_f1_score
    }
    pickle.dump(train_val_stats, open(os.path.join(stats_logdir, "train_val_stats.pickle"), "wb"))

    
    # ------------------------------ Evaluation ------------------------------
    # Plot and save figures for training stats
    training_curves(train_loss, val_loss, train_acc, val_acc, stats_logdir)


# PC Local paths
model_logdir = r"C:\Users\xmoot\Desktop\Models\TensorFlow\ssl-seizure-detection\models"
stats_logdir = r"C:\Users\xmoot\Desktop\Models\TensorFlow\ssl-seizure-detection\stats"
pseudodata_path = r"C:\Users\xmoot\Desktop\Data\ssl-seizure-detection\patient_pseudolabeled\relative_positioning\jh101_12s_7min_np.pkl"

# Load data
data = pickle.load(open(pseudodata_path, "rb"))

# Hyperparameters
fltrs_out=64
l2_reg=1e-3
lr=1e-3
epochs=100
batch_size=32
val_size=0.2
test_size=0
seed=0
es_patience=20
num_examples=50000

run(data=data, fltrs_out=fltrs_out, l2_reg=l2_reg, lr=lr, epochs=epochs, batch_size=batch_size, val_size=val_size, test_size=test_size,
    seed=seed, es_patience=es_patience, stats_logdir=stats_logdir, model_logdir=model_logdir, num_examples=num_examples)

# Takes approximately 1.5min to run 1000 examples
print("Process finished --- %s seconds ---" % (time.time() - start_time))