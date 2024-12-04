function [U,L,Xm] = pca(X,K)
%PCA  Principal Component Analysis.
%   [U,L,Xm] = pca(X) creates an eigenspace from data matrix X.
%   It returns mean image Xm, eigenvectors in columns of U and eigenvalues L.
%   Each column of X is a vector representing an image.
%   [U,L,Xm] = pca(X,K) returns only the first K eigenvectors and eigenvalues.
if nargin < 2
    K = size(X, 2);
end
[M N]=size(X);
Xm=mean(X,2);
% if isa(X, 'single')
%     subcol_single(X, Xm);
% else
    X=subcol(X, Xm);
    %       X = X - repmat(Xm, 1, size(X, 2));
% end

if (N < M) %less images than image length
    C=X'*X;
    [V D Vt]=svds(double(C), K);
    V = cast(V, class(X)); D = cast(D, class(X)); Vt = cast(Vt, class(X));
    U=X*V;
    denom = repmat(sqrt(diag(D)'),M,1);
    denom(denom == 0) = 1;
    U=U./denom;
else %more images than image length
    C=X*X';
    [U D Ut]=svd(C);
end;
L=diag(D)'/N;

if nargin>1
    U=U(:,1:min(K, size(U, 2)));
    L=L(1:min(K, size(L, 2)));
end;
