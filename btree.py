
class BTreeBuilder:

   MAX_TREE_DEPTH      = 8    # Maximum tree depth.
   MIN_TRIANGLE_COUNT  = 2    # Minimum number of triangles in a node.
   MAX_EXTRA_TRIANGLES = 50.0 # Maximum number of triangles created during division (percent).
   MIN_CHILD_NODE_SIZE = 25.0 # Minimum size of a child node relative to its parent (percent).
   MIN_LEAF_NODE_SIZE  = 1.0  # Minimum size of a leaf node relative to the root node (percent).
   MIN_ALGORITHM_STEP  = 0.1  # Minimum algorithm step relative to the size of a node (percent).

   # Divide a line segment into two parts based on the given division axis and value.
   # Create a new vertex at the point of division, and return its index.
   # Division value must be between the two specified vertices!
   def divide_line_segment(self, div_axis, div_value, vix1, vix2):
      v1 = self.vertices[vix1][div_axis]
      v2 = self.vertices[vix2][div_axis]
      f = (v2 - div_value) / (v2 - v1)
      c = [(self.colors   [vix1][i] * f + self.colors   [vix2][i] * (1.0-f)) for i in range(4)]
      t = [(self.texcoords[vix1][i] * f + self.texcoords[vix2][i] * (1.0-f)) for i in range(2)]
      v = [(self.vertices [vix1][i] * f + self.vertices [vix2][i] * (1.0-f)) for i in range(2)]
      self.colors.append(tuple(c))
      self.texcoords.append(tuple(t))
      self.vertices.append(tuple(v))
      return (len(self.vertices) - 1)

   def divide_triangle(self, div_axis, div_value, triangle_indexes):
      i1,i2,i3 = sorted(triangle_indexes, key = lambda i: self.vertices[i][div_axis])
      # | v1 v2 v3
      if (self.vertices[i1][div_axis] >= div_value):
         return [], [(i1, i2, i3)]
      # v1 v2 v3 |
      elif (self.vertices[i3][div_axis] <= div_value):
         return [(i1, i2, i3)], []
      # v1 v|2 v3
      elif (self.vertices[i2][div_axis] == div_value):
         i4 = self.divide_line_segment(div_axis, div_value, i1, i3)
         return [(i1, i2, i4)], [(i2, i3, i4)]
      # v1 | v2 v3
      elif (self.vertices[i2][div_axis] > div_value):
         i4 = self.divide_line_segment(div_axis, div_value, i1, i2)
         i5 = self.divide_line_segment(div_axis, div_value, i1, i3)
         return [(i1, i4, i5)], [(i2, i3, i4), (i3, i4, i5)]
      # v1 v2 | v3
      else:
         i4 = self.divide_line_segment(div_axis, div_value, i1, i3)
         i5 = self.divide_line_segment(div_axis, div_value, i2, i3)
         return [(i1, i2, i4), (i2, i4, i5)], [(i3, i4, i5)]

   # Return the number of triangles in each node for the specified division axis and value.
   def try_triangles_division(self, div_axis, div_value, triangles):
      n1,n2 = 0,0
      for triangle_indexes in triangles:
         i1,i2,i3 = sorted(triangle_indexes, key = lambda i: self.vertices[i][div_axis])
         # | v1 v2 v3
         if (self.vertices[i1][div_axis] >= div_value):
            n2 += 1
         # v1 v2 v3 |
         elif (self.vertices[i3][div_axis] <= div_value):
            n1 += 1
         # v1 v|2 v3
         elif (self.vertices[i2][div_axis] == div_value): 
            n1 += 1
            n2 += 1
         # v1 | v2 v3
         elif (self.vertices[i2][div_axis] > div_value):
            n1 += 1
            n2 += 2
         # v1 v2 | v3
         else:
            n1 += 2
            n2 += 1
      return (n1,n2)

   def calculate_division_score(self, div_axis, div_value, min_value, max_value, count_total, count1, count2):
      count_extra = (count1 + count2) - count_total
      count_diff = abs(count1 - count2)
      size_total = max_value - min_value
      # Each node must have enough triangles.
      if (count1 < BTreeBuilder.MIN_TRIANGLE_COUNT) or (count2 < BTreeBuilder.MIN_TRIANGLE_COUNT):
         return None
      # The number of added triangles must be relatively small.
      if (float(count_extra) / float(count_total)) > (BTreeBuilder.MAX_EXTRA_TRIANGLES / 100.0):
         return None
      # Child node must not be too small relatively to its parent and the root node.
      size1 = div_value - min_value
      size2 = max_value - div_value
      if (min(size1, size2) / size_total) < (BTreeBuilder.MIN_CHILD_NODE_SIZE / 100.0):
         return None
      if (min(size1, size2) / self.root_size[div_axis]) < (BTreeBuilder.MIN_LEAF_NODE_SIZE / 100.0):
         return None
      # Penalty for any added triangle, and for difference in triangle counts.
      score = (count_extra + count_diff)
      # Score is inversely proportional to the size. This is to make the nodes
      # more square-ish (better score when dividing the longer side of a rectangle).
      score /= size_total
      return score

   def determine_division_value(self, div_axis, triangles):

      def flatten(lst):
         return [item for sublist in lst for item in sublist]

      triangles_flat = flatten(triangles)
      coords_sorted = [self.vertices[i][div_axis] for i in triangles_flat]
      coords_sorted.sort()
      min_value = coords_sorted[0]
      max_value = coords_sorted[-1]
      min_step = (max_value - min_value) * (BTreeBuilder.MIN_ALGORITHM_STEP / 100.0)
      # Try division at the middle vertex first.
      div_index = len(coords_sorted)//2
      div_value = coords_sorted[div_index]
      n1,n2 = self.try_triangles_division(div_axis, div_value, triangles)
      score = self.calculate_division_score(div_axis, div_value, min_value, max_value, len(triangles), n1, n2)
      # This is our best try so far.
      best_score = score
      best_value = div_value
      # If the first node has less triangles than the second node, then try to
      # decrease division value and see if the score is better. If the first node
      # has more triangles, then try to increase division value instead.
      di = 0
      if (n1 < n2): di = -1
      if (n1 > n2): di = +1
      while True:
         if best_score == 0:
            break
         elif (di < 0) and (n1 < n2) and (div_index > 0):
            div_index += di
         elif (di > 0) and (n1 > n2) and (div_index < len(coords_sorted)-1):
            div_index += di
         else:
            break
         if abs(div_value - coords_sorted[div_index]) >= min_step:
            div_value = coords_sorted[div_index]
            n1,n2 = self.try_triangles_division(div_axis, div_value, triangles)
            score = self.calculate_division_score(div_axis, div_value, min_value, max_value, len(triangles), n1, n2)
            if (score is not None) and ((best_score is None) or (best_score > score)):
               best_score = score
               best_value = div_value
      # Return the best result.
      return (best_score, best_value)

   def create_tree_node(self, triangles, depth):
      div_axis  = None
      div_value = None
      if (depth > 1) and (len(triangles) > 0):
         # Determine the division axis and value.
         score_x, value_x = self.determine_division_value(0, triangles)
         score_y, value_y = self.determine_division_value(1, triangles)
         if (score_x is not None) or (score_y is not None):
            if score_x is None:
               score_x = float('inf')
            if score_y is None:
               score_y = float('inf')
            if score_x < score_y:
               div_axis  = 0
               div_value = value_x
            else:
               div_axis  = 1
               div_value = value_y
      if div_axis is not None:
         # Divide triangles.
         triangles1, triangles2 = [],[]
         for triangle_indexes in triangles:
            t1,t2 = self.divide_triangle(div_axis, div_value, triangle_indexes)
            triangles1 += t1
            triangles2 += t2
         # Create child nodes.
         node1 = self.create_tree_node(triangles1, depth-1)
         node2 = self.create_tree_node(triangles2, depth-1)
         return {
            'kind': 'branch',
            'div_axis': div_axis,
            'div_value': div_value,
            'node1': node1,
            'node2': node2}
      else:
         return {
            'kind': 'leaf',
            'triangles': triangles}

   def determine_root_size(self):
      if len(self.vertices) > 0:
         min_x, min_y = self.vertices[0]
         max_x, max_y = self.vertices[0]
         for v in self.vertices:
            if min_x > v[0]: min_x = v[0]
            if max_x < v[0]: max_x = v[0]
            if min_y > v[1]: min_y = v[1]
            if max_y < v[1]: max_y = v[1]
         self.root_size = [(max_x - min_x), (max_y - min_y)]

   def divide_polygons_into_triangles(self, polygons):
      self.triangles = []
      for poly in polygons:
         if poly:
            for i in range(0, len(poly), 3):
               self.triangles.append((poly[i], poly[i+1], poly[i+2]))

   # Remove vertices which are not referenced by any triangle. Rearange vertices
   # so that near ones in space are also near themselves in the vertex table.
   def filter_and_sort_vertices(self):
      dct = {}
      lst = []

      def process_tree_node(node):
         if node['kind'] == 'branch':
            process_tree_node(node['node1'])
            process_tree_node(node['node2'])
         else:
            triangles = node['triangles']
            for i in range(len(triangles)):
               for vix in triangles[i]:
                  if vix not in dct:
                     dct[vix] = len(lst)
                     lst.append(vix)
               triangles[i] = tuple([dct[vix] for vix in triangles[i]])

      process_tree_node(self.root)
      self.colors    = [self.colors   [i] for i in lst]
      self.texcoords = [self.texcoords[i] for i in lst]
      self.vertices  = [self.vertices [i] for i in lst]

   def build(self, polygons, colors, texcoords, vertices):
      self.colors    = colors
      self.texcoords = texcoords
      self.vertices  = vertices
      self.determine_root_size()
      self.divide_polygons_into_triangles(polygons)
      self.root = self.create_tree_node(self.triangles, BTreeBuilder.MAX_TREE_DEPTH)
      self.filter_and_sort_vertices()
      return {
         'root':      self.root,
         'colors':    self.colors,
         'texcoords': self.texcoords,
         'vertices':  self.vertices}
