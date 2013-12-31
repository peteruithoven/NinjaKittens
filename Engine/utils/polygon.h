#ifndef UTILS_POLYGON_H
#define UTILS_POLYGON_H

#include <vector>
using std::vector;
#include "clipper/clipper.hpp"

#include "utils/intpoint.h"

class Polygons
{
private:
    ClipperLib::Paths polygons;
public:
    unsigned int size()
    {
        return polygons.size();
    }
    
    ClipperLib::Path& operator[] (int index) //__attribute__((__deprecated__))
    {
        return polygons[index];
    }
    void remove(int index)
    {
        polygons.erase(polygons.begin() + index);
    }
    void clear()
    {
        polygons.clear();
    }
    void add(const ClipperLib::Path& poly)
    {
        polygons.push_back(poly);
    }
    void add(const Polygons& other)
    {
        for(unsigned int n=0; n<other.polygons.size(); n++)
            polygons.push_back(other.polygons[n]);
    }
    
    Polygons() {}
    Polygons(const Polygons& other) { polygons = other.polygons; }
    Polygons& operator=(const Polygons& other) { polygons = other.polygons; return *this; }
    Polygons difference(const Polygons& other) const
    {
        Polygons ret;
        ClipperLib::Clipper clipper;
        clipper.AddPaths(polygons, ClipperLib::ptSubject, true);
        clipper.AddPaths(other.polygons, ClipperLib::ptClip, true);
        clipper.Execute(ClipperLib::ctDifference, ret.polygons);
        return ret;
    }
    Polygons unionPolygons(const Polygons& other) const
    {
        Polygons ret;
        ClipperLib::Clipper clipper;
        clipper.AddPaths(polygons, ClipperLib::ptSubject, true);
        clipper.AddPaths(other.polygons, ClipperLib::ptSubject, true);
        clipper.Execute(ClipperLib::ctUnion, ret.polygons, ClipperLib::pftNonZero, ClipperLib::pftNonZero);
        return ret;
    }
    Polygons intersection(const Polygons& other) const
    {
        Polygons ret;
        ClipperLib::Clipper clipper;
        clipper.AddPaths(polygons, ClipperLib::ptSubject, true);
        clipper.AddPaths(other.polygons, ClipperLib::ptClip, true);
        clipper.Execute(ClipperLib::ctIntersection, ret.polygons);
        return ret;
    }
    Polygons offset(int distance) const
    {
        Polygons ret;
        ClipperLib::ClipperOffset clipper;
        clipper.AddPaths(polygons, ClipperLib::jtMiter, ClipperLib::etClosedPolygon);
        clipper.MiterLimit = 2.0;
        clipper.Execute(ret.polygons, distance);
        return ret;
    }
    vector<Polygons> splitIntoParts(bool unionAll = false) const
    {
        vector<Polygons> ret;
        ClipperLib::Clipper clipper;
        ClipperLib::PolyTree resultPolyTree;
        clipper.AddPaths(polygons, ClipperLib::ptSubject, true);
        if (unionAll)
            clipper.Execute(ClipperLib::ctUnion, resultPolyTree, ClipperLib::pftNonZero, ClipperLib::pftNonZero);
        else
            clipper.Execute(ClipperLib::ctUnion, resultPolyTree);
        
        _processPolyTreeNode(&resultPolyTree, ret);
        return ret;
    }
    Polygons processEvenOdd() const
    {
        Polygons ret;
        ClipperLib::Clipper clipper;
        clipper.AddPaths(polygons, ClipperLib::ptSubject, true);
        clipper.Execute(ClipperLib::ctUnion, ret.polygons);
        return ret;
    }
    
    bool orientation(int n)
    {
        return ClipperLib::Orientation(polygons[n]);
    }

    double area(int n)
    {
        return ClipperLib::Area(polygons[n]);
    }
    
    Point centerOfMass(int idx)
    {
        double x = 0, y = 0;
        Point p0 = polygons[idx][polygons[idx].size()-1];
        for(unsigned int n=0; n<polygons[idx].size(); n++)
        {
            Point p1 = polygons[idx][n];
            double second_factor = (p0.X * p1.Y) - (p1.X * p0.Y);
            
            x += double(p0.X + p1.X) * second_factor;
            y += double(p0.Y + p1.Y) * second_factor;
            p0 = p1;
        }

        double a = area(idx);
        x = x / 6 / a;
        y = y / 6 / a;

        if (x < 0)
        {
            x = -x;
            y = -y;
        }
        return Point(x, y);
    }
private:
    void _processPolyTreeNode(ClipperLib::PolyNode* node, vector<Polygons>& ret) const
    {
        for(int n=0; n<node->ChildCount(); n++)
        {
            ClipperLib::PolyNode* child = node->Childs[n];
            Polygons polygons;
            polygons.add(child->Contour);
            for(int i=0; i<child->ChildCount(); i++)
            {
                polygons.add(child->Childs[i]->Contour);
                _processPolyTreeNode(child->Childs[i], ret);
            }
            ret.push_back(polygons);
        }
    }
public:
    int64_t polygonLength() const
    {
        int64_t length = 0;
        for(unsigned int i=0; i<polygons.size(); i++)
        {
            Point p0 = polygons[i][polygons[i].size()-1];
            for(unsigned int n=0; n<polygons[i].size(); n++)
            {
                Point p1 = polygons[i][n];
                length += vSize(p0 - p1);
                p0 = p1;
            }
        }
        return length;
    }

    void applyMatrix(const PointMatrix& matrix)
    {
        for(unsigned int i=0; i<polygons.size(); i++)
        {
            for(unsigned int j=0; j<polygons[i].size(); j++)
            {
                polygons[i][j] = matrix.apply(polygons[i][j]);
            }
        }
    }
};

/* Axis aligned boundary box */
class AABB
{
public:
    Point min, max;
    
    AABB()
    : min(LLONG_MIN, LLONG_MIN), max(LLONG_MIN, LLONG_MIN)
    {
    }
    AABB(Polygons polys)
    : min(LLONG_MIN, LLONG_MIN), max(LLONG_MIN, LLONG_MIN)
    {
        calculate(polys);
    }
    
    void calculate(Polygons polys)
    {
        min = Point(LLONG_MAX, LLONG_MAX);
        max = Point(LLONG_MIN, LLONG_MIN);
        for(unsigned int i=0; i<polys.size(); i++)
        {
            for(unsigned int j=0; j<polys[i].size(); j++)
            {
                if (min.X > polys[i][j].X) min.X = polys[i][j].X;
                if (min.Y > polys[i][j].Y) min.Y = polys[i][j].Y;
                if (max.X < polys[i][j].X) max.X = polys[i][j].X;
                if (max.Y < polys[i][j].Y) max.Y = polys[i][j].Y;
            }
        }
    }
    
    bool hit(const AABB& other) const
    {
        if (max.X < other.min.X) return false;
        if (min.X > other.max.X) return false;
        if (max.Y < other.min.Y) return false;
        if (min.Y > other.max.Y) return false;
        return true;
    }
};

#endif//UTILS_POLYGON_H