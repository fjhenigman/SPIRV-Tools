# Copyright (c) 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

if (${SPIRV_BUILD_FUZZER})

  set(SOURCES
          fuzz_test_util.h

          fuzzer_replayer_test.cpp
          fact_manager_test.cpp
          fuzz_test_util.cpp
          transformation_add_constant_boolean_test.cpp
          transformation_add_constant_scalar_test.cpp
          transformation_add_dead_break_test.cpp
          transformation_add_type_boolean_test.cpp
          transformation_add_type_float_test.cpp
          transformation_add_type_int_test.cpp
          transformation_move_block_down_test.cpp
          transformation_replace_boolean_constant_with_constant_binary_test.cpp
          transformation_split_block_test.cpp)

  add_spvtools_unittest(TARGET fuzz
        SRCS ${SOURCES}
        LIBS SPIRV-Tools-fuzz
        )
endif()
