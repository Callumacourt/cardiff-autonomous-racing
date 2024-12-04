function [W, E] = triangulate_bbox(bboxL, bboxR, P1, P2)

W = []; E = [];
[w, e] = triangulate_point(bboxL(1:2)', bboxR(1:2)', P1, P2);
W = [W w(:)]; E = [E e];
            
[w, e] = triangulate_point([bboxL(1) + bboxL(3) bboxL(2)]', ...
    [bboxR(1) + bboxR(3) bboxR(2)]', P1, P2);
W = [W w(:)]; E = [E e];

[w, e] = triangulate_point([bboxL(1) bboxL(2) + bboxL(4)]', ...
    [bboxR(1) bboxR(2) + bboxR(4)]', P1, P2);
W = [W w(:)]; E = [E e];

[w, e] = triangulate_point([bboxL(1) + bboxL(3) bboxL(2) + bboxL(4)]', ...
    [bboxR(1) + bboxR(3) bboxR(2) + bboxR(4)]', P1, P2);
W = [W w(:)]; E = [E e];
