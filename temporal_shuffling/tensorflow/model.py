from spektral.layers import ECCConv, GlobalAvgPool, GATConv
import tensorflow as tf
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.regularizers import l2


class gnn_encoder(Model):
    def __init__(self, fltrs_out=64, l2_reg=1e-3):
        super(gnn_encoder, self).__init__()
        
        # Encoder
        self.conv1 = ECCConv(fltrs_out, kernel_network=[32], activation="relu", kernel_regularizer=l2(l2_reg))
        
        self.conv2 = GATConv(fltrs_out, activation="relu", kernel_regularizer=l2(l2_reg),
                             attn_kernel_regularizer=l2(l2_reg), return_attn_coef=True)
        self.flatten = GlobalAvgPool()
        
        #TODO: Create an expander
        
        # Embedding
        self.fc = Dense(32, "relu", kernel_regularizer=l2(l2_reg))
        
        
    def call(self, inputs):
        A_in, X_in, E_in = inputs

        x = self.conv1([X_in, A_in, E_in])

        x, attn = self.conv2([x, A_in])

        x = self.flatten(x)

        x = self.fc(x)
        
        return x
    

class regression(Model):
    def __init__(self):
        super(regression, self).__init__()

        self.fc = Dense(1, activation = None)

    def call(self, x, version):
        x = self.fc(x)

        # Logistic regression
        if version == "log":
            return tf.sigmoid(x)
        
        # Linear regression
        else:
            return x


class temporal_shuffling(Model):
    def __init__(self, fltrs_out=64, l2_reg=1e-3):
        super(temporal_shuffling, self).__init__()
        self.gnn_encoder = gnn_encoder(fltrs_out, l2_reg)
        self.regression = regression()
        
    def call(self, inputs):
        
        # Graph pairs
        graph_1, graph_2, graph_3 = inputs
        
        # Encode the graphs
        z_1 = self.gnn_encoder(graph_1)
        z_2 = self.gnn_encoder(graph_2)
        z_3 = self.gnn_encoder(graph_3)
        
        # Contrast their encodings
        x = tf.abs(z_1 - z_2)
        
        # Return logistic regression of the contrastive component
        return self.regression(x, "log")



# # Test case
# import numpy as np
# np.random.seed(16)
# tf.random.set_seed(16)

# # Define number of nodes, edges, and features
# N = 10  # Number of nodes
# F = 5   # Number of node features
# S = 2   # Number of edge features
# E = N * (N - 1) // 2 # Number of edges

# # Generate random input graph data
# A_1, A_2 = (np.random.rand(N, N), np.random.rand(N, N)) # Adjacency matrix
# X_1, X_2 = (np.random.rand(N, F), np.random.rand(N, F))  # Node features
# E_1, E_2 = (np.random.rand(N * N, S), np.random.rand(N * N, S))  # Edge features for all possible edges


# # Instantiate the different modules
# encoder = gnn_encoder()
# contrast_layer = contrast()
# regression_layer = regression()

# # Encode the graph
# z_1 = encoder.call([A_1, X_1, E_1])
# z_2 = encoder.call([A_2, X_2, E_2])

# # Compute contrastive embedding
# x = contrast_layer([z_1, z_2])

# # Perform regression on the contrasted result
# regression_output = regression_layer(x, version="log")

# # Print the results
# print("Encoded Graph 1:", z_1)
# print("Encoded Graph 2:", z_2)
# print("Contrasted Embedding:", x)
# print("Regression Output:", regression_output)