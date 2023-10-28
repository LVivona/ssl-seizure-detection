import sys
from train import train


if __name__ == '__main__':

    # The path to .pt file of Data, PairData, or TripletData objects list
    data_path = sys.argv[1]
    
    # Path to save the model, statistics, and training information
    logdir = sys.argv[2]
    
    # Patient identifier
    patient_id = str(sys.argv[3])
    
    # Model identifier
    model_id = str(sys.argv[4])

    # Date and time identifier
    datetime_id = str(sys.argv[5])

    # Run identifier
    run_type = str(sys.argv[6])

    # Transfer learning (optional arguments)
    # Initialize variables to None
    model_path=None
    model_dict_path=None
    transfer_id=None
    frozen=None

    # Check the number of arguments and set variables accordingly
    if len(sys.argv) > 7:
        model_path = str(sys.argv[7])
        model_dict_path = str(sys.argv[8])
        transfer_id = str(sys.argv[9])
        frozen = bool(int(sys.argv[10]))


    # Node feature dimension configuration (some patients have less node features)
    if patient_id in {"ummc003", "ummc004", "ummc006"}:
        num_node_features = 7 
    elif patient_id in {"ummc001", "ummc002"}:
        num_node_features = 8
    else:
        num_node_features = 9

    
    # Training parameters
    epochs=200
    val_ratio=0.2
    test_ratio=0.1
    
    if model_id == "supervised":
        config = {
            "num_node_features": num_node_features,
            "num_edge_features": 3,
            "hidden_channels": 64,
            "out_channels": 32,
            "dropout": 0.1,
        }
        data_size=1.0
        test_ratio=0.1

    elif model_id == "relative_positioning" or model_id == "temporal_shuffling":
        config = {
        "num_node_features": num_node_features,
        "num_edge_features": 3,
        "hidden_channels": [64, 32, 64, 128, 256],
        }
        data_size=115000

    elif model_id == "downstream1":
        config = {
        "hidden_channels": [64, 64, 32],
        "dropout": 0.1,
        }
        data_size=1.0
    
    train(data_path, logdir, patient_id, epochs, config, data_size, val_ratio, test_ratio, 
          batch_size=32, num_workers=4, lr=1e-3, weight_decay=1e-3, model_id=model_id, timing=True, 
          classify="binary", head="linear", dropout=True, datetime_id=datetime_id, run_type=run_type, 
          frozen=frozen, model_path=model_path, model_dict_path=model_dict_path, transfer_id=transfer_id)
