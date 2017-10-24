import tensorflow as tf
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
#from scipy.spatial import Delaunay

timeN = 2
numsubleg = 3
numLeg = 4
Mtot = 0.9849
dtime = 0.01
Fupscale = 1.
Fdownscale = 0.5
Fricscale = Mtot*9.81*1.
wall = tf.constant([1.])
g = tf.constant([[0,0,-9.81]],dtype=tf.float32)
Fup = tf.constant([[0,0,Mtot*Fupscale*9.81]],dtype=tf.float32)
Fdown = tf.constant([[0,0,Mtot*Fdownscale*9.81]],dtype=tf.float32)
Fadded = tf.constant([[0,0,Mtot*(Fupscale+Fdownscale)*9.81/2.]],dtype=tf.float32)
Fsubed = tf.constant([[0,0,Mtot*(Fupscale-Fdownscale)*9.81]],dtype=tf.float32)  
Offset = tf.constant([[0,0,0.5]],dtype=tf.float32)
V_goal = tf.constant([[0.06,0.,0.]], dtype = tf.float32)
truetensor = tf.constant([True],dtype=tf.bool)

#Theta lock
theta_ub = [tf.constant([np.pi/5.]), tf.constant([-np.pi/6.]), tf.constant([np.pi/5.])]
theta_lb = [tf.constant([-np.pi/8.]), tf.constant([-np.pi/1.5]), tf.constant([-np.pi/8.])]

#Variables
global_step = tf.Variable(0,trainable = False, name = 'global_step')
W1=tf.Variable(tf.random_uniform([33,20], -1, 1,dtype=tf.float32), dtype=tf.float32)
W2=tf.Variable(tf.random_uniform([20,12], -1, 1,dtype=tf.float32), dtype=tf.float32)
b1 = tf.Variable(tf.zeros([20]))

class Rigidbody:
    def __init__(self,m=0.0,Q=tf.eye(3,dtype=tf.float32),Ib=tf.zeros((3,3),dtype=tf.float32),wb=tf.zeros((1,3),dtype=tf.float32)):
        self.m = m
        self.Q = Q
        self.Ib = Ib
        self.wb = wb
       
class Robotbody(Rigidbody):
    def __init__(self,m=0.0, rs=tf.zeros((1,3), dtype=tf.float32), vs=tf.zeros((1,3), dtype=tf.float32), lbtomot = [tf.zeros((1,3),dtype=tf.float32) for _ in range(numLeg)]):
        Rigidbody.__init__(self,m=m)
        self.lbtomot=[tf.zeros((1,3),dtype=tf.float32) for _ in range(numLeg)]
        self.lbtomot[0] = lbtomot[0]
        self.lbtomot[1] = lbtomot[1]
        self.lbtomot[2] = lbtomot[2]
        self.lbtomot[3] = lbtomot[3]
        self.rs = rs
        self.vs = vs
        self.lbtomot = lbtomot

class subleg(Rigidbody):
    def __init__(self,m=0.0,axis=tf.zeros((1,3),dtype=tf.float32),l = [tf.zeros((1,3),dtype=tf.float32) for _ in range(2)],theta=tf.zeros([1]),omega=tf.zeros([1]),alpha=tf.zeros([1])):
        Rigidbody.__init__(self,m=m)
        self.axis = axis
        self.l=[tf.zeros((1,3),dtype=tf.float32) for _ in range(2)]
        self.l[0] = l[0]
        self.l[1] = l[1]
        self.theta = theta
        self.omega = omega
        self.alpha = alpha

class Leg:
    def __init__(self):
        self.sub = [subleg() for _ in range(numsubleg)]

class robot:
    def __init__(self):
        self.body = Robotbody()
        self.leg = [Leg() for _ in range(numLeg)]

    def set_constants(self):
        
        self.body.rs = tf.constant([[0,0,0.25]], dtype = tf.float32)
        self.body.vs = tf.zeros([1,3], dtype = tf.float32)
        self.body.wb = tf.zeros([1,3], dtype = tf.float32)
        self.body.Q = tf.constant([[1,0,0],[0,1,0],[0,0,1]], dtype = tf.float32)
        #Set Axes
        self.leg[0].sub[0].axis = tf.constant([[0.,1.,0.]],dtype=tf.float32)
        self.leg[0].sub[1].axis = tf.constant([[1.,0.,0.]],dtype=tf.float32)
        self.leg[0].sub[2].axis = tf.constant([[1.,0.,0.]],dtype=tf.float32)

        self.leg[1].sub[0].axis = tf.constant([[0.,-1.,0.]],dtype=tf.float32)
        self.leg[1].sub[1].axis = tf.constant([[1.,0.,0.]],dtype=tf.float32)
        self.leg[1].sub[2].axis = tf.constant([[1.,0.,0.]],dtype=tf.float32)

        self.leg[2].sub[0].axis = tf.constant([[0.,1.,0.]],dtype=tf.float32)
        self.leg[2].sub[1].axis = tf.constant([[-1.,0.,0.]],dtype=tf.float32)
        self.leg[2].sub[2].axis = tf.constant([[-1.,0.,0.]],dtype=tf.float32)

        self.leg[3].sub[0].axis = tf.constant([[0.,-1.,0.]],dtype=tf.float32)
        self.leg[3].sub[1].axis = tf.constant([[-1.,0.,0.]],dtype=tf.float32)
        self.leg[3].sub[2].axis = tf.constant([[-1.,0.,0.]],dtype=tf.float32)

        #Set lvectors
        self.body.lbtomot[0] = tf.constant([[0.065,0.065,0.02]],dtype=tf.float32)
        self.body.lbtomot[1] = tf.constant([[-0.065,0.065,0.02]],dtype=tf.float32)
        self.body.lbtomot[2] = tf.constant([[0.065,-0.065,0.02]],dtype=tf.float32)
        self.body.lbtomot[3] = tf.constant([[-0.065,-0.065,0.02]],dtype=tf.float32)

        self.leg[0].sub[0].l[0] = tf.constant([[0.,0.020,0.0]],dtype=tf.float32)
        self.leg[0].sub[0].l[1] = tf.constant([[0.,0.,-0.015]],dtype=tf.float32)
        self.leg[0].sub[1].l[0] = tf.constant([[0.,0.033,0.]],dtype=tf.float32)
        self.leg[0].sub[1].l[1] = tf.constant([[0.,0.033,0.]],dtype=tf.float32)
        self.leg[0].sub[2].l[0] = tf.constant([[0.,0.030,0.]],dtype=tf.float32)
        self.leg[0].sub[2].l[1] = tf.constant([[0.,0.070,0.]],dtype=tf.float32)

        self.leg[1].sub[0].l[0] = tf.constant([[0.,0.020,0.0]],dtype=tf.float32)
        self.leg[1].sub[0].l[1] = tf.constant([[0.,0.,-0.015]],dtype=tf.float32)
        self.leg[1].sub[1].l[0] = tf.constant([[0.,0.033,0.]],dtype=tf.float32)
        self.leg[1].sub[1].l[1] = tf.constant([[0.,0.033,0.]],dtype=tf.float32)
        self.leg[1].sub[2].l[0] = tf.constant([[0.,0.030,0.]],dtype=tf.float32)
        self.leg[1].sub[2].l[1] = tf.constant([[0.,0.070,0.]],dtype=tf.float32)

        self.leg[2].sub[0].l[0] = tf.constant([[0.,-0.020,0.]],dtype=tf.float32)
        self.leg[2].sub[0].l[1] = tf.constant([[0.,0.,-0.015]],dtype=tf.float32)
        self.leg[2].sub[1].l[0] = tf.constant([[0.,-0.033,0.]],dtype=tf.float32)
        self.leg[2].sub[1].l[1] = tf.constant([[0.,-0.033,0.]],dtype=tf.float32)
        self.leg[2].sub[2].l[0] = tf.constant([[0.,-0.030,0.]],dtype=tf.float32)
        self.leg[2].sub[2].l[1] = tf.constant([[0.,-0.070,0.]],dtype=tf.float32)

        self.leg[3].sub[0].l[0] = tf.constant([[0.,-0.020,0.]],dtype=tf.float32)
        self.leg[3].sub[0].l[1] = tf.constant([[0.,0.,-0.015]],dtype=tf.float32)
        self.leg[3].sub[1].l[0] = tf.constant([[0.,-0.033,0.]],dtype=tf.float32)
        self.leg[3].sub[1].l[1] = tf.constant([[0.,-0.033,0.]],dtype=tf.float32)
        self.leg[3].sub[2].l[0] = tf.constant([[0.,-0.030,0.]],dtype=tf.float32)
        self.leg[3].sub[2].l[1] = tf.constant([[0.,-0.070,0.]],dtype=tf.float32)

        #set Mass
        for p in range(numLeg):
            self.leg[p].sub[0].m = tf.constant(0.0550,dtype=tf.float32) #kg
            self.leg[p].sub[1].m = tf.constant(0.0294,dtype=tf.float32)
            self.leg[p].sub[2].m = tf.constant(0.0709,dtype=tf.float32)

            #set Inertia tensors
            self.leg[p].sub[0].Ib = tf.constant([[1.62e-5,0.,0.],
                                                 [0.,1.87e-5,0.],
                                                 [0.,0.,1.20e-5]],dtype=tf.float32)

            self.leg[p].sub[1].Ib = tf.constant([[0.60e-5,0.,0.],
                                                 [0.,0.30e-5,0.],
                                                 [0.,0.,0.60e-5]],dtype=tf.float32)

            self.leg[p].sub[2].Ib = tf.constant([[2.00e-5,0.,0.],
                                                 [0.,1.40e-5,0.],
                                                 [0.,0.,2.20e-5]],dtype=tf.float32)
            #set Initial theta conditions
            '''
            for i in range(numsubleg):
                self.leg[p].sub[i].theta = tf.constant(0., dtype=tf.float32)
            '''
            self.leg[p].sub[1].theta = tf.constant(-np.pi / 2., dtype=tf.float32)

        self.body.m = (0.2676 + 0.1414) \
                      +self.leg[0].sub[0].m \
                      -self.leg[0].sub[1].m \
                      -self.leg[0].sub[2].m \
                      +(0.1583 + 0.2358)

        Mtot = self.body.m + 4 * (self.leg[0].sub[0].m+self.leg[0].sub[1].m+self.leg[0].sub[2].m)

        self.body.Ib = tf.constant([[75.0e-5,0.,0.],
                                    [0.,75.0e-5,0.],
                                    [0.,0.,50.0e-5]],dtype=tf.float32)
        
    def timeflow(self,t = 0.0):
        Momentum = tf.matmul(tf.matmul(self.body.wb, self.body.Ib), self.body.Q) + tf.scalar_mul(self.body.m , tf.cross(self.body.rs, self.body.vs))
        Feqc = tf.scalar_mul(Mtot, g)
        Feqa = tf.diag([Mtot, Mtot, Mtot])
        Crossvec = tf.zeros((1,3), dtype=tf.float32)
        Teqalpha = tf.zeros((3,3), dtype=tf.float32)
        Teqc = tf.zeros((1,3), dtype=tf.float32)
        mlsum = tf.zeros((1,3), dtype=tf.float32)
        sumDs = tf.zeros((3,3), dtype=tf.float32)
        wbs = tf.matmul(self.body.wb, self.body.Q) #[1,3] matrix
        tot_lbtomots = []
        for p in range(numLeg):
           for i in range(numsubleg):
               self.leg[p].sub[i].omega += self.leg[p].sub[i].alpha * dtime #omega를 시간에 따라 갱신
               self.leg[p].sub[i].theta += self.leg[p].sub[i].omega * dtime #theta를 시간에 따라 갱신
               #print(tf.reshape(self.leg[p].sub[i].theta, []))
               #print(tf.constant(1.)-tf.reshape(tf.cos(self.leg[p].sub[i].theta),[]))
               self.leg[p].sub[i].Q = tf.scalar_mul( tf.reshape(tf.cos(self.leg[p].sub[i].theta),[] ) , tf.eye(3, dtype=tf.float32)) + \
               tf.scalar_mul(tf.constant(1.)-tf.reshape(tf.cos(self.leg[p].sub[i].theta), []), tf.matmul(self.leg[p].sub[i].axis, self.leg[p].sub[i].axis, transpose_a = True)) + \
               tf.scalar_mul(tf.sin(tf.reshape(self.leg[p].sub[i].theta,[])), tf.cross(tf.tile(self.leg[p].sub[i].axis,[3,1]), tf.eye(3, dtype=tf.float32)))
           Qs = [tf.matmul(self.leg[p].sub[0].Q , self.body.Q)] #Qs는 i번째 subleg에서 space로의 좌표변환
           #List of rotation matrices of each sublegs in space frame
           #Type : list of [3,3] Tensor
           for i in range(1,numsubleg):
               Qs.append(tf.matmul(self.leg[p].sub[i].Q , Qs[i-1]))

           Is = [ tf.matmul( tf.matmul(Qs[i] , self.leg[p].sub[i].Ib, transpose_a = True) , Qs[i]) for i in range(numsubleg) ]

           e = [tf.matmul(self.leg[p].sub[i].axis, Qs[i]) for i in range(numsubleg)]
           #List of axes of each sublegs in space frame
           #Type : list of [None,3] Tensor

           Qalpha = [tf.scalar_mul(tf.reshape(self.leg[p].sub[i].alpha,[]),e[i]) for i in range(numsubleg)]
           
           Qalphasum = [ Qalpha[0] ]
           for i in range(1,numsubleg): Qalphasum.append( Qalphasum[i-1] + Qalpha[i] )

           Qw = [tf.scalar_mul(tf.reshape(self.leg[p].sub[i].omega,[]),e[i]) for i in range(numsubleg)]

           ws = [wbs+Qw[0]]
           for i in range(1,numsubleg): 
               ws.append(ws[i-1] + Qw[i])

           w = [tf.matmul(ws[i], Qs[i], transpose_b = True) for i in range(numsubleg)]

           ls = [[tf.matmul(self.leg[p].sub[i].l[0],Qs[i]), 
                  tf.matmul(self.leg[p].sub[i].l[1],Qs[i])] for i in range(numsubleg)] #ls = 2Dtensor

           lbtomotbs = tf.matmul(self.body.lbtomot[p] , self.body.Q) # lbtomotbs = 2Dtensor

           lbtomots = [ lbtomotbs + ls[0][0] ] # lbtomots = 2Dtensor

           for i in range(1,numsubleg):
               lbtomots.append(lbtomots[i-1]+ls[i-1][1]+ls[i][0])
           for i in range(numsubleg):
               mlsum += tf.scalar_mul(self.leg[p].sub[i].m, lbtomots[i])
           #각운동량 디버깅용
           vmotbs = [tf.cross(wbs, lbtomotbs)+tf.cross(ws[0],ls[0][0])]
           for i in range(1, numsubleg):
               vmotbs.append(vmotbs[i-1]+tf.cross(ws[i-1],ls[i-1][1])+tf.cross(ws[i],ls[i][0]))

           #Calculating External Forces
           vs = self.body.vs
           for i in range(numsubleg):
               Collisiontemp = tf.cast(tf.less(lbtomots[i]+ls[i][1]+self.body.rs,tf.zeros((1,3),dtype=tf.float32)),tf.float32)
               Collisionz = tf.multiply(Collisiontemp, tf.constant([[0,0,1]], tf.float32))
               Collisionxy = tf.matmul(Collisionz, tf.constant([[0,0,0],[0,0,0],[1,1,0]], tf.float32))##더 연산량을 줄일 수 있을 듯 방법을 강구하라
               vs += tf.cross(ws[i], ls[i][0]+ls[i][1])
               vCollision = tf.cast(tf.less( vs , tf.zeros((1,3),dtype=tf.float32) ),tf.float32)
               Ftemp = tf.multiply(Collisionz, Fadded + tf.multiply( (vCollision - Offset) , Fsubed ))
               Feqc += Ftemp
               Teqc += tf.cross( lbtomots[i] + ls[i][1], Ftemp )
               FrictionTemp = -tf.multiply(tf.scalar_mul( Fricscale , vs ), Collisionxy)##########하.. 힘이 너무 다 틀렸어
               Feqc += FrictionTemp
               Teqc += tf.cross( lbtomots[i] + ls[i][1], FrictionTemp )
           
           A = [tf.cross(wbs,tf.cross(wbs,lbtomotbs))
                + tf.cross(Qalphasum[0],ls[0][0])
                + tf.cross(ws[0], tf.cross(ws[0],ls[0][0]))]

           for i in range(1,numsubleg):
               A.append(
                        tf.cross( Qalphasum[i-1], ls[i-1][1] )
                        +tf.cross( Qalphasum[i], ls[i][0])
                        +tf.cross( ws[i-1], tf.cross(ws[i-1], ls[i-1][1]))
                        +tf.cross( ws[i], tf.cross(ws[i], ls[i][0]))
                   )

           mlsquare = tf.zeros((1),dtype=tf.float32)
           for i in range(numsubleg):
               mlsquare += tf.scalar_mul(self.leg[p].sub[i].m,
                                         tf.matmul(lbtomots[i],lbtomots[i],transpose_b=True))
           mlsquare = tf.reshape(mlsquare,[-1])
           Dya = tf.zeros([3,3], dtype = tf.float32)
           for i in range(numsubleg):
               Dya += tf.scalar_mul(self.leg[p].sub[i].m,tf.matmul(lbtomots[i],lbtomots[i],transpose_a=True))
           ###############
           Ds = tf.diag(tf.concat([mlsquare,mlsquare,mlsquare], axis=0)) - Dya
           Teqalpha += Ds
           sumDs += Ds
           #Qb * Ib * Qb.transpose()

           for i in range(numsubleg):
               Feqc -= tf.scalar_mul(self.leg[p].sub[i].m,A[i])
               Crossvec += tf.scalar_mul(self.leg[p].sub[i].m,lbtomots[i])
               Teqc += tf.matmul( tf.cross( tf.matmul(w[i] , self.leg[p].sub[i].Ib) , w[i] ), Qs[i])
               Teqc -= tf.matmul( Qalphasum[i] , Is[i])
               Teqalpha += Is[i]
               #Qs_i * I_i * Qs_i^T
           for i in range(numsubleg):
               Momentum += tf.matmul(tf.matmul(w[i], self.leg[p].sub[i].Ib), Qs[i])
               Momentum += tf.scalar_mul(self.leg[p].sub[i].m, tf.cross(lbtomots[i] + self.body.rs, vmotbs[i]+self.body.vs))
           #leg update
           #float32 -> float64 conversion : 171013 Fine
               #update 'Q's of leg - 20171012 fine
           tot_lbtomots += lbtomots
        Teqalpha += tf.matmul( tf.matmul( self.body.Q , self.body.Ib, transpose_a = True) , self.body.Q)
        Teqc += tf.matmul( tf.cross( tf.matmul( self.body.wb , self.body.Ib ), self.body.wb) , self.body.Q)
        Teqc += tf.cross(mlsum, g)
        Teqanorm = tf.reduce_sum(tf.square(mlsum))
        alphabs = tf.matmul(
            Teqc - tf.scalar_mul(1./Mtot, tf.cross(mlsum,Feqc)),
            tf.matrix_inverse(
                Teqalpha + tf.scalar_mul(1./Mtot , 
                Teqanorm*tf.eye(3, dtype = tf.float32) - tf.matmul(mlsum,mlsum,transpose_a = True))#여기가 너무 헷갈림.......
            )
        )
        asb = tf.scalar_mul(1./Mtot, Feqc - tf.cross(mlsum,alphabs))
        alphab = tf.matmul(alphabs, self.body.Q, transpose_b = True)
        self.body.wb += tf.scalar_mul(dtime, alphab)
        self.body.Q += tf.scalar_mul(dtime,tf.cross(tf.concat([wbs, wbs, wbs], axis = 0),self.body.Q))
        self.body.vs += tf.scalar_mul(dtime,asb)
        self.body.rs += tf.scalar_mul(dtime,self.body.vs)

        # Q to quaternion
        
        qw = tf.scalar_mul(0.5, tf.sqrt(tf.reduce_sum(tf.diag_part(self.body.Q))+1.))
        qv = -tf.reduce_sum(tf.cross(self.body.Q, tf.eye(3, dtype = tf.float32)), axis = 0)/tf.scalar_mul(4., qw)

        # quaternion normalization

        qvsquare = tf.reduce_sum(tf.square(qv))
        qnorm = tf.sqrt(tf.square(qw)+qvsquare)
        qw /= qnorm
        qv /= qnorm
        # quaternion to Q

        self.body.Q = tf.scalar_mul(qw*qw-qvsquare,tf.eye(3, dtype = tf.float32))\
            + 2. * tf.matmul(tf.reshape(qv, [3, 1]), tf.reshape(qv, [1, 3]))\
            + 2. * qw * tf.cross(tf.tile(tf.reshape(qv, [1,3]), [3,1]), tf.eye(3, dtype = tf.float32))

R = robot()
R.set_constants()
print("set constant")

cost = tf.constant(0.0, dtype = tf.float32)

arrtheta = []

for time in range(timeN):
    print(time)
    inlay=[]
    for p in range (numLeg):
        for i in range(numsubleg):
            inlay = tf.concat([inlay, tf.reshape( R.leg[p].sub[i].theta, [1])], axis = 0)
            inlay = tf.concat([inlay, tf.reshape( R.leg[p].sub[i].omega, [1])], axis = 0)

    inlay = tf.concat([inlay, tf.tile(tf.reshape(tf.slice(R.body.Q,[2,0],[1,3]), [-1]), [3])], axis = 0)

    inlay = tf.reshape(inlay, [1,33])

    L1 = tf.nn.relu(tf.matmul(inlay, W1))+b1
    L2 = tf.nn.tanh(tf.matmul(L1, W2))
    for p in range(numLeg):
        for i in range(numsubleg):
            L2, alphatemp = tf.split(L2, [-1, 1], 1)
            R.leg[p].sub[i].alpha = alphatemp

            thlock_ub = tf.cast(tf.greater(R.leg[p].sub[i].theta, theta_ub[i]),dtype=tf.float32)
            thlock_lb = tf.cast(tf.less(R.leg[p].sub[i].theta, theta_lb[i]),dtype=tf.float32)
            #print('thlock_ub = ',wall)
            R.leg[p].sub[i].alpha += tf.multiply(thlock_ub, - R.leg[p].sub[i].alpha - wall)
            R.leg[p].sub[i].alpha += tf.multiply(thlock_lb, - R.leg[p].sub[i].alpha + wall) #Restricting theta

    R.timeflow()
    cost += tf.reduce_mean(tf.square(R.body.vs-V_goal))

optimizer = tf.train.AdamOptimizer(learning_rate=10)
train_op=optimizer.minimize(cost)

sess = tf.Session()
'''
init=tf.global_variables_initializer()
sess=tf.Session()
sess.run(init)
'''

nowrs = np.array([[0,0,0.1]])
nowvs = np.zeros((1,3))
nowwb = np.zeros((1,3))
nowQb = np.array([[1,0,0],[0,1,0],[0,0,1]])

ckpt = tf.train.get_checkpoint_state('./model')
if ckpt and tf.train.checkpoint_exists(ckpt.model_checkpoint_path):
    saver.restore(sess,ckpt.model_checkpoint_path)
else:
    sess.run(tf.global_variables_initializer())

for i in range(100000):
    _, printcost = sess.run([train_op, cost])
    if i%100 == 0:
        print("cost = ", printcost)
        for p in range(numLeg):
            for j in range(numsubleg):
                print("alpha : ",sess.run(R.leg[p].sub[j].alpha),end=' ')
                print("omega : ",sess.run(R.leg[p].sub[j].omega),end=' ')
                print("theta : ",sess.run(R.leg[p].sub[j].theta),end='\n')

        saver = tf.train.Saver(tf.global_variables())
        saver.save(sess, './model/RobotNN.ckpt',global_step = global_step)