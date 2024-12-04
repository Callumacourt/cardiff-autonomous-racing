#include "mex.h"
#include "Simd/SimdDetection.hpp"
#include "Simd/SimdDrawing.hpp"
#include "Simd/SimdPoint.hpp"
#include "Test/TestUtils.h"
#include "Test/TestPerformance.h"
#include "Test/TestData.h"

#include <ctime>
using namespace std;
using namespace Simd;
void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {
  if (Simd::Sse41::Enable)
    {
      mexPrintf("!\n");
    }
  
  
  typedef Simd::Detection<Simd::Allocator> Detection;
  Detection::View image;
  image.Load("lena.pgm");
  Detection detection;
  detection.Load("haar_face_0.xml");
  detection.Init(image.Size(), 1.1, Point<int>(10, 12), Point<int>(10 * 6, 12 * 6));
  Detection::Objects objects;

  clock_t begin = clock();

  int iter = 10;
  for (int i = 0; i < iter; ++i) {
    detection.Detect(image, objects, 1, 0.0);
  }

  clock_t end = clock();

  double elapsed_secs = double(end - begin) / CLOCKS_PER_SEC;
  mexPrintf("%f ms\n", elapsed_secs * 1000.0 / (double)iter);

  for (size_t i = 0; i < objects.size(); ++i)
    Simd::DrawRectangle(image, objects[i].rect, uint8_t(255));
  image.Save("result.pgm");  
}
