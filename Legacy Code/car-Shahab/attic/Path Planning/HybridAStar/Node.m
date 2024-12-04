classdef Node < handle
    properties (Constant)
        %number of units in a meter (scale)
        s = 30*0.5
        %cell size in meters
        cs = 1*Node.s
        %distance travelled in one motion primitive
        d = 1.35*Node.cs
        %vehicle length and width
        vlen = 1.3*Node.s
        vwidth = 0.8*Node.s
        vmaxd = sqrt((Node.vlen/2).^2+(Node.vwidth/2).^2)
        %center point collision range 
        cr = 0.8*Node.vmaxd
        %corner points collision range
        ccr = 0.3*Node.cs
        %steering angles to expand on in neighbours in degrees
        %is converted to radians
        %range is half of full range, so range for a turn in one direction
        %maximum steering angle
        amax = 35
        %number of angles
        na = 7
        angles = deg2rad(linspace(-Node.amax,Node.amax,Node.na))
        ia = Node.angles(1) - Node.angles(2)
    end
    properties
        x 
        y
        theta
        %current steering angle of the vehicle alpha
        a
        %cost
        g
        %cost + heuristic
        f
        %parent in discovered path
        parent
        %number of nodes away from start node
        n
    end
    methods
        function obj = Node(x, y, theta, alpha, g, parent, n)
            if nargin > 5
                obj.x = x;
                obj.y = y;
                obj.theta =  theta;
                obj.a = alpha;
                obj.g = g;
                obj.parent = parent;
                obj.n = n;
            elseif nargin > 3
                obj.x = x;
                obj.y = y;
                obj.theta = theta;
                obj.a = alpha;
            elseif nargin > 0
                obj.x = 0;
                obj.y = 0;
                obj.theta =  0;
                obj.g = 0;
            end
        end
        
        function ns = getMotionPrimitives(obj)
            ns(1:numel(Node.angles)) = Node();
            for i = 1:numel(Node.angles)
                m = obj.applyMotion(Node.angles(i));
                ns(i) = m; 
            end
        end
        
        %takes a motion as input steering angle (alpha)
        %returns a node after performing the motion
        %function res = applyMotion(obj, alpha, d, length)
        function res = applyMotion(obj, alpha)
            %turning angle beta
            beta = Node.d/Node.vlen * tan(alpha);
            %straight motion
            if abs(beta) > 0.0001
                r = Node.d/beta;
                cx = obj.x - sin(obj.theta)*r;
                cy = obj.y + cos(obj.theta)*r;
                tf_x = cx + sin(obj.theta+beta)*r;
                tf_y = cy - cos(obj.theta+beta)*r;
            else
                tf_x = obj.x + Node.d * cos(obj.theta);
                tf_y = obj.y + Node.d * sin(obj.theta);
            end
            tf_theta = mod(obj.theta+beta,2*pi);
            res = Node(tf_x, tf_y, tf_theta, alpha);
        end
        
        %equal, greater/less than functions
        function res = eq(n1, n2)
            if (n1.x == n2.x) && (n1.y == n2.y)
                res = 1;
                return
            end
            res = 0;
        end
        
        function res = gt(n1, n2)
            if isa(n1, 'Node') && isa(n2, 'Node')
                if (n1.f > n2.f)
                    res = 1;
                    return
                %tie breaker
                elseif (n1.f == n2.f)
                    if (n1.g < n2.g)
                        res = 1;
                        return
                    end
                end
                res = 0;
            elseif ~isa(n1, 'Node')
                if (n1 > n2.f)
                    res = 1;
                    return
                end
                res = 0;
            elseif ~isa(n2, 'Node')
                if (n1.f > n2)
                    res = 1;
                    return
                end
                res = 0;
            end
        end
        
        function res = ge(n1, n2)
            if isa(n1, 'Node') & isa(n2, 'Node')
                if (n1.f >= n2.f)
                    res = 1;
                    return
                end
                res = 0;
            elseif ~isa(n1, 'Node')
                if (n1 >= n2.f)
                    res = 1;
                    return
                end
                res = 0;
            elseif ~isa(n2, 'Node')
                if (n1.f >= n2)
                    res = 1;
                    return
                end
                res = 0;
            end
        end
        
        function res = lt(n1, n2)
            if isa(n1, 'Node') & isa(n2, 'Node')
                if (n1.f < n2.f)
                    res = 1;
                    return
                %tie breaker
                elseif (n1.f == n2.f)
                    if (n1.g > n2.g)
                        res = 1;
                        return
                    end
                end
                res = 0;
            elseif ~isa(n1, 'Node')
                if (n1 < n2.f)
                    res = 1;
                    return
                end
                res = 0;
            elseif ~isa(n2, 'Node')
                if (n1.f < n2)
                    res = 1;
                    return
                end
                res = 0;
            end
        end
        
        function res = le(n1, n2)
            if isa(n1, 'Node') & isa(n2, 'Node')
                if (n1.f <= n2.f)
                    res = 1;
                    return
                end
                res = 0;
            elseif ~isa(n1, 'Node')
                if (n1 <= n2.f)
                    res = 1;
                    return
                end
                res = 0;
            elseif ~isa(n2, 'Node')
                if (n1.f <= n2)
                    res = 1;
                    return
                end
                res = 0;
            end
        end
    end
end